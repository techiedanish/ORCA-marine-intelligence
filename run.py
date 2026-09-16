#!/usr/bin/env python3
"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Single-Port Launcher
========================================================================================
The ONE command that starts the entire platform:

    python run.py

What it does:
  1. If apps/web3/node_modules is missing, runs `npm install`.
  2. If apps/web3/out (the static export) is missing OR --rebuild is passed, runs
     `npm run build` to statically export the Next.js frontend.
  3. Installs Python dependencies from apps/api/requirements.txt if fastapi isn't
     already importable in the current interpreter.
  4. Starts the FastAPI app (apps/api/main.py), which serves the exported frontend
     at "/" AND the API at "/api/v1/*" on a single port (default 8000).

Cross-platform: works on Windows, macOS, and Linux (uses shutil.which to locate
`npm`/`npm.cmd` and subprocess with the correct shell semantics for each OS).

Flags:
  --port 8000        Change the port (default 8000, or $PORT if set)
  --skip-build        Skip the frontend build step even if apps/web3/out is missing
  --rebuild           Force a frontend rebuild even if apps/web3/out already exists
========================================================================================
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
API_DIR = ROOT / "apps" / "api"
WEB_DIR = ROOT / "apps" / "web3"
WEB_OUT = WEB_DIR / "out"
WEB_NODE_MODULES = WEB_DIR / "node_modules"


def find_npm() -> str:
    npm = shutil.which("npm")
    if npm:
        return npm
    # Windows sometimes only exposes npm.cmd on PATH depending on install method
    npm_cmd = shutil.which("npm.cmd")
    if npm_cmd:
        return npm_cmd
    print(
        "ERROR: npm was not found on PATH. Install Node.js (https://nodejs.org) "
        "and re-run `python run.py`.",
        file=sys.stderr,
    )
    sys.exit(1)


def run(cmd, cwd):
    print(f"\n$ {' '.join(cmd)}   (in {cwd})")
    result = subprocess.run(cmd, cwd=str(cwd), shell=(os.name == "nt"))
    if result.returncode != 0:
        print(f"ERROR: command failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)


def ensure_python_deps():
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
        import httpx  # noqa: F401
        import pydantic  # noqa: F401
    except ImportError:
        print("Python backend dependencies missing — installing from requirements.txt…")
        run(
            [sys.executable, "-m", "pip", "install", "-r", str(API_DIR / "requirements.txt")],
            cwd=ROOT,
        )


def check_google_maps_key():
    env_local = WEB_DIR / ".env.local"
    key_value = ""
    if env_local.exists():
        for line in env_local.read_text().splitlines():
            if line.strip().startswith("NEXT_PUBLIC_GOOGLE_MAPS_API_KEY="):
                key_value = line.split("=", 1)[1].strip()
                break
    if not key_value:
        print(
            "\n"
            "NOTE: No NEXT_PUBLIC_GOOGLE_MAPS_API_KEY found in apps/web3/.env.local.\n"
            "      The app will still start, but the map panel will show a\n"
            "      'Google Maps API key required' message instead of the chart.\n"
            "      Get a free key and see where to put it in the root README.md\n"
            "      (section: 'Getting a free Google Maps API key'), then run:\n"
            "      python run.py --rebuild\n"
        )


def ensure_frontend_built(skip_build: bool, force_rebuild: bool):
    check_google_maps_key()

    if skip_build:
        if not WEB_OUT.exists():
            print(
                "WARNING: --skip-build was passed but apps/web3/out does not exist. "
                "The API will start, but '/' will show an API-only index until you build the frontend."
            )
        return

    npm = find_npm()

    if not WEB_NODE_MODULES.exists():
        print("Frontend dependencies not installed — running `npm install`…")
        run([npm, "install"], cwd=WEB_DIR)

    if force_rebuild or not WEB_OUT.exists():
        print("Building the static frontend export (`npm run build`)…")
        run([npm, "run", "build"], cwd=WEB_DIR)
    else:
        print(f"Using existing frontend build at {WEB_OUT} (pass --rebuild to force a fresh build).")


def start_backend(port: int):
    # Import after dependency check so a missing-package error doesn't happen at
    # module-import time with a confusing traceback.
    sys.path.insert(0, str(API_DIR))
    os.environ.setdefault("PORT", str(port))
    os.chdir(API_DIR)  # so main.py's relative paths (data/, etc.) resolve correctly

    import uvicorn

    print(f"\nORCA is starting on http://localhost:{port}  (single port — UI + API)")
    print(f"API docs available at http://localhost:{port}/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)


def main():
    parser = argparse.ArgumentParser(description="ORCA single-port launcher")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    parser.add_argument("--skip-build", action="store_true", help="Don't build/check the frontend")
    parser.add_argument("--rebuild", action="store_true", help="Force a fresh frontend build")
    args = parser.parse_args()

    ensure_python_deps()
    ensure_frontend_built(skip_build=args.skip_build, force_rebuild=args.rebuild)
    start_backend(port=args.port)


if __name__ == "__main__":
    main()
