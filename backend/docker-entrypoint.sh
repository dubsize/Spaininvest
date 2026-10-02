#!/bin/sh
set -e

wait_for_db() {
  python - <<'PY'
import sys, time
from sqlalchemy import create_engine, text
from arbscan.core.config import get_settings
url = get_settings().database_url
for i in range(60):
    try:
        with create_engine(url).connect() as c:
            c.execute(text("SELECT 1"))
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        print(f"waiting for database ({exc.__class__.__name__})", flush=True)
        time.sleep(2)
sys.exit("database not reachable")
PY
}

case "$1" in
  api)
    wait_for_db
    python -m arbscan.cli migrate
    python -m arbscan.cli seed
    exec uvicorn arbscan.api.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
    ;;
  worker)
    wait_for_db
    exec celery -A arbscan.workers.celery_app:celery_app worker --loglevel=INFO --concurrency=${WORKER_CONCURRENCY:-2}
    ;;
  beat)
    wait_for_db
    exec celery -A arbscan.workers.celery_app:celery_app beat --loglevel=INFO --schedule /tmp/celerybeat-schedule
    ;;
  *)
    exec "$@"
    ;;
esac
