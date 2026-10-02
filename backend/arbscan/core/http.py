"""Polite HTTP client used by every connector.

* per-host token-bucket rate limiting (Redis-backed when available, so several workers
  share one budget; in-process fallback otherwise)
* retries with exponential backoff + jitter on network errors, 429 and 5xx, honouring
  ``Retry-After``
* robots.txt enforcement for page fetches (official APIs are exempt: they are governed
  by their own terms and rate limits)
* identifies itself with a descriptive User-Agent; optional proxy only if configured
"""

from __future__ import annotations

import random
import threading
import time
import urllib.robotparser
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from arbscan.core.config import get_settings
from arbscan.core.logging import get_logger

log = get_logger(__name__)


class RobotsDisallowed(Exception):
    pass


class RateLimited(Exception):
    pass


class HttpError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class RetryPolicy:
    max_attempts: int = 4
    base_delay: float = 1.0
    max_delay: float = 30.0
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504)


class TokenBucket:
    """In-process token bucket (requests per minute)."""

    def __init__(self, per_minute: float):
        self.capacity = max(1.0, per_minute / 6)  # allow small bursts
        self.rate = per_minute / 60.0
        self.tokens = self.capacity
        self.updated = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self, timeout: float = 120.0) -> None:
        deadline = time.monotonic() + timeout
        while True:
            with self.lock:
                now = time.monotonic()
                self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
                self.updated = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                wait = (1 - self.tokens) / self.rate
            if time.monotonic() + wait > deadline:
                raise RateLimited("local rate limit budget exhausted")
            time.sleep(min(wait, 5))


class RedisRateLimiter:
    """Fixed-window limiter shared across processes."""

    def __init__(self, redis_client: Any, key: str, per_minute: int):
        self.r = redis_client
        self.key = key
        self.per_minute = per_minute

    def acquire(self, timeout: float = 120.0) -> None:
        deadline = time.monotonic() + timeout
        while True:
            window = int(time.time() // 60)
            k = f"ratelimit:{self.key}:{window}"
            n = self.r.incr(k)
            if n == 1:
                self.r.expire(k, 70)
            if n <= self.per_minute:
                return
            sleep = 60 - (time.time() % 60) + random.uniform(0, 1)
            if time.monotonic() + sleep > deadline:
                raise RateLimited(f"rate limit for {self.key} exhausted")
            time.sleep(min(sleep, 10))


_robots: dict[str, tuple[float, urllib.robotparser.RobotFileParser | None]] = {}
_lock = threading.Lock()


_limiters: dict[str, Any] = {}


def _limiter(key: str, per_minute: int) -> Any:
    """Shared Redis limiter when Redis is reachable, otherwise an in-process bucket.
    The choice is cached per key for the life of the process."""
    with _lock:
        if key in _limiters:
            return _limiters[key]
    settings = get_settings()
    limiter: Any
    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=2)
        client.ping()
        limiter = RedisRateLimiter(client, key, per_minute)
    except Exception:
        limiter = TokenBucket(per_minute)
    with _lock:
        _limiters.setdefault(key, limiter)
        return _limiters[key]


class PoliteClient:
    def __init__(
        self,
        name: str,
        requests_per_minute: int = 10,
        retry: RetryPolicy | None = None,
        enforce_robots: bool = True,
        transport: httpx.BaseTransport | None = None,
    ):
        s = get_settings()
        self.name = name
        self.retry = retry or RetryPolicy()
        self.enforce_robots = enforce_robots and s.respect_robots_txt
        self.requests_per_minute = requests_per_minute
        ua = s.http_user_agent + (f" contact:{s.http_contact}" if s.http_contact else "")
        self.client = httpx.Client(
            timeout=s.http_timeout_seconds,
            headers={"User-Agent": ua, "Accept-Language": "es,fr;q=0.9,de;q=0.8,en;q=0.7"},
            proxy=s.http_proxy or None,
            follow_redirects=True,
            transport=transport,
        )
        self.ua = ua
        self.stats = {"requests": 0, "retries": 0, "errors": 0}

    # ------------------------------------------------------------------ robots
    def allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        now = time.time()
        cached = _robots.get(base)
        if not cached or now - cached[0] > 3600:
            rp: urllib.robotparser.RobotFileParser | None = urllib.robotparser.RobotFileParser()
            try:
                resp = self.client.get(f"{base}/robots.txt", timeout=10)
                if resp.status_code >= 400:
                    # 4xx -> no robots.txt -> allowed; 5xx -> be conservative
                    rp = None if resp.status_code < 500 else False  # type: ignore[assignment]
                else:
                    assert rp is not None
                    rp.parse(resp.text.splitlines())
            except httpx.HTTPError:
                rp = False  # type: ignore[assignment]
            _robots[base] = (now, rp)
            cached = _robots[base]
        rp = cached[1]
        if rp is None:
            return True
        if rp is False:
            return False
        return rp.can_fetch(self.ua, url)

    # ------------------------------------------------------------------ request
    def request(self, method: str, url: str, *, check_robots: bool | None = None, **kwargs: Any) -> httpx.Response:
        if (self.enforce_robots if check_robots is None else check_robots) and not self.allowed(url):
            raise RobotsDisallowed(f"robots.txt disallows {url}")
        limiter = _limiter(f"{self.name}:{urlparse(url).netloc}", self.requests_per_minute)
        last_exc: Exception | None = None
        for attempt in range(1, self.retry.max_attempts + 1):
            limiter.acquire()
            self.stats["requests"] += 1
            try:
                resp = self.client.request(method, url, **kwargs)
            except httpx.HTTPError as exc:
                last_exc = exc
                self._sleep(attempt, None, f"network error: {exc}")
                continue
            if resp.status_code in self.retry.retry_statuses and attempt < self.retry.max_attempts:
                self.stats["retries"] += 1
                self._sleep(attempt, resp.headers.get("Retry-After"), f"HTTP {resp.status_code}")
                continue
            if resp.status_code >= 400:
                self.stats["errors"] += 1
                raise HttpError(f"{method} {url} -> HTTP {resp.status_code}: {resp.text[:300]}", resp.status_code)
            return resp
        self.stats["errors"] += 1
        raise HttpError(f"{method} {url} failed after {self.retry.max_attempts} attempts: {last_exc}")

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def _sleep(self, attempt: int, retry_after: str | None, reason: str) -> None:
        if retry_after and retry_after.isdigit():
            delay = min(float(retry_after), self.retry.max_delay * 4)
        else:
            delay = min(self.retry.max_delay, self.retry.base_delay * 2 ** (attempt - 1))
            delay *= random.uniform(0.7, 1.3)
        log.warning("http retry", extra={"client": self.name, "attempt": attempt, "delay": round(delay, 2), "reason": reason})
        time.sleep(delay)

    def close(self) -> None:
        self.client.close()
