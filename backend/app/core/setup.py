from pathlib import Path
import sys

# Optional dotenv; Vercel may omit it, so guard the import.
try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover

    def load_dotenv(*args, **kwargs):
        return False


def apply_initial_setup():
    # Ensure `app` package is importable both locally and in serverless.
    backend_dir = Path(__file__).resolve().parents[2]  # .../backend
    for p in {backend_dir, backend_dir.parent}:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

    # Load environment variables (.env at repo root preferred, fallback to backend/.env)
    repo_root_env = backend_dir.parent / ".env"
    backend_env = backend_dir / ".env"
    if repo_root_env.exists():
        load_dotenv(dotenv_path=repo_root_env, override=True)
    elif backend_env.exists():
        load_dotenv(dotenv_path=backend_env, override=True)
    else:
        load_dotenv(override=True)
