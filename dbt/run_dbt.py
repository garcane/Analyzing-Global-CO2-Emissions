"""Run dbt with this project's settings.

    uv run python dbt/run_dbt.py build
    uv run python dbt/run_dbt.py debug
    uv run python dbt/run_dbt.py build --target prod

Why a wrapper: dbt does not read .env, and on networks that inspect TLS it needs the operating system's
certificate store (same as ingestion/cli.py). This loads .env, injects the system certificates, fixes the
project and profiles directories, then calls dbt's own entry point. Arguments pass straight through.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")

try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

from dbt.cli.main import dbtRunner


def main() -> int:
    args = sys.argv[1:] + ["--project-dir", str(HERE), "--profiles-dir", str(HERE)]
    result = dbtRunner().invoke(args)
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
