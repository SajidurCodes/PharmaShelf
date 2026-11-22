import json
import os
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def wait_for_embeddings() -> None:
    base_url = os.getenv("EMBEDDING_BASE_URL", "http://embeddings").rstrip("/")
    request = Request(
        f"{base_url}/embed",
        data=b'{"inputs": "PharmaShelf startup check"}',
        headers={"Content-Type": "application/json"},
    )
    deadline = time.monotonic() + 600
    print("Waiting for the embedding model...", flush=True)

    while True:
        try:
            with urlopen(request, timeout=10) as response:
                vectors = json.load(response)

            if (
                not isinstance(vectors, list)
                or len(vectors) != 1
                or not isinstance(vectors[0], list)
                or len(vectors[0]) != 384
            ):
                raise ValueError("Expected one 384-dimensional embedding")

            return

        except HTTPError as exc:
            if exc.code not in (502, 503, 504):
                raise
        except (URLError, TimeoutError, ConnectionError):
            pass

        if time.monotonic() >= deadline:
            raise RuntimeError("Embedding service did not become ready in 10 minutes")

        time.sleep(3)


def main() -> None:
    python = sys.executable

    subprocess.run([python, "-m", "alembic", "upgrade", "head"], check=True)
    subprocess.run([python, "-m", "scripts.seed_demo_users"], check=True)
    subprocess.run([python, "-m", "scripts.seed_inventory"], check=True)
    subprocess.run([python, "-m", "scripts.seed_almanac"], check=True)

    wait_for_embeddings()
    subprocess.run([python, "-m", "scripts.ingest_almanac"], check=True)

    os.execv(
        python,
        [
            python, "-m", "uvicorn", "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
        ],
    )


if __name__ == "__main__":
    main()