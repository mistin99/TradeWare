"""Application container entrypoint that runs migrations before the API."""

import subprocess
import sys


def main() -> None:
    """Apply database migrations and then execute the requested command."""
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    command = sys.argv[1:]
    if not command:
        raise SystemExit("No application command was provided")
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
