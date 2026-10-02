"""Command line: ``python -m arbscan.cli <command>``.

Commands: migrate | seed [--demo] | demo-purge | scan <marketplace> | analysis | hash-password
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from arbscan.core.config import get_settings
from arbscan.core.logging import configure_logging


def migrate() -> None:
    from alembic.config import Config

    from alembic import command

    cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parent.parent / "alembic"))
    command.upgrade(cfg, "head")


def main(argv: list[str] | None = None) -> int:
    s = get_settings()
    configure_logging(s.log_level, s.log_json)
    p = argparse.ArgumentParser(prog="arbscan")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate")
    sp = sub.add_parser("seed")
    sp.add_argument("--demo", action="store_true", help="also load demo listings (if none yet)")
    sub.add_parser("demo-purge")
    sc = sub.add_parser("scan")
    sc.add_argument("marketplace")
    sub.add_parser("analysis")
    sub.add_parser("hash-password")
    args = p.parse_args(argv)

    if args.cmd == "migrate":
        migrate()
    elif args.cmd == "seed":
        from arbscan.db.session import session_scope
        from arbscan.seed.loader import seed_demo_data, seed_reference_data

        with session_scope() as session:
            print("reference:", seed_reference_data(session))
        if args.demo or s.seed_demo_data:
            with session_scope() as session:
                print("demo:", seed_demo_data(session))
    elif args.cmd == "demo-purge":
        from arbscan.db.session import session_scope
        from arbscan.seed.loader import purge_demo_data

        with session_scope() as session:
            print("deleted demo listings:", purge_demo_data(session))
    elif args.cmd == "scan":
        from arbscan.db.session import session_scope
        from arbscan.services.scanner import run_marketplace_scan

        with session_scope() as session:
            run = run_marketplace_scan(session, args.marketplace, force=True)
            print(f"{run.status}: found={run.listings_found} new={run.listings_new} updated={run.listings_updated} "
                  f"opportunities={run.opportunities_created} error={run.error or '-'}")
    elif args.cmd == "analysis":
        from arbscan.workers.tasks import analysis

        print(analysis())
    elif args.cmd == "hash-password":
        from arbscan.api.security import hash_password

        pw = getpass.getpass("Password: ")
        print(hash_password(pw))
    return 0


if __name__ == "__main__":
    sys.exit(main())
