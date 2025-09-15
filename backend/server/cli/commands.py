import sys
import subprocess
from pathlib import Path
from typing import Iterable

from server.settings import DATABASE_PATHS


def _alembic_ini() -> str:
    return str(Path(__file__).resolve().parents[1] / "alembic.ini")


def _run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.run(cmd).returncode


def _db_list(db_name: str | None) -> list[str]:
    if db_name:
        if db_name not in DATABASE_PATHS:
            valid = ", ".join(DATABASE_PATHS.keys())
            raise SystemExit(f"Unknown db '{db_name}'. Valid: {valid}")
        return [db_name]
    # preserve insertion order from settings
    return list(DATABASE_PATHS.keys())


def make_migration() -> None:
    """Create autogenerate revisions.

    Usage:
      - poetry run make-migration                     -> all DBs, message 'auto'
      - poetry run make-migration <db>                -> one DB, message 'auto'
      - poetry run make-migration <db> <msg...>       -> one DB, custom message
      - poetry run make-migration <msg...>            -> all DBs, custom message
    """
    args = sys.argv[1:]

    db_name: str | None = None
    message = "auto"

    if args:
        if args[0] in DATABASE_PATHS:
            db_name = args[0]
            message = " ".join(args[1:]).strip() or message
        else:
            message = " ".join(args).strip() or message

    failures = 0
    for db in _db_list(db_name):
        cmd = [
            "alembic",
            "-c",
            _alembic_ini(),
            "-x",
            f"db={db}",
            "revision",
            "--autogenerate",
            "-m",
            message,
        ]
        code = _run(cmd)
        failures += int(code != 0)

    raise SystemExit(1 if failures else 0)


def migrate() -> None:
    """Upgrade database(s) to a given target (default: head).

    Usage:
      - poetry run migrate                            -> all DBs to head
      - poetry run migrate <db>                       -> one DB to head
      - poetry run migrate <db> <target>              -> one DB to <target>
      - poetry run migrate <target>                   -> all DBs to <target>
    """
    args = sys.argv[1:]

    db_name: str | None = None
    target = "head"

    if args:
        if args[0] in DATABASE_PATHS:
            db_name = args[0]
            if len(args) > 1:
                target = args[1]
        else:
            target = args[0]

    failures = 0
    for db in _db_list(db_name):
        cmd = [
            "alembic",
            "-c",
            _alembic_ini(),
            "-x",
            f"db={db}",
            "upgrade",
            target,
        ]
        code = _run(cmd)
        failures += int(code != 0)

    raise SystemExit(1 if failures else 0)

