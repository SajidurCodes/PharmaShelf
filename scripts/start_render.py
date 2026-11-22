import os
import subprocess
import sys


def main() -> None:
    python = sys.executable

    subprocess.run([python, "-m", "alembic", "upgrade", "head"], check=True)
    subprocess.run([python, "-m", "scripts.seed_inventory"], check=True)

    port = os.environ.get("PORT", "8000")
    os.execv(
        python,
        [python, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port],
    )


if __name__ == "__main__":
    main()