"""
MuleGuard Unified Startup Runner
Starts the complete MuleGuard application (FastAPI backend + frontend static assets).
Handles port conflict resolution and environment validation automatically.
"""

import os
import sys
import time
import socket
import subprocess

# Ensure running inside project directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)

# Auto-switch to .venv python if needed
VENV_PYTHON = os.path.join(PROJECT_DIR, ".venv", "Scripts", "python.exe")
if os.path.exists(VENV_PYTHON):
    current_python = os.path.normpath(sys.executable).lower()
    venv_python_norm = os.path.normpath(VENV_PYTHON).lower()
    if current_python != venv_python_norm:
        # Check if current python has uvicorn/fastapi, else re-exec
        try:
            import fastapi  # noqa
            import uvicorn  # noqa
        except ImportError:
            print(f"[MuleGuard] Switching to virtualenv python: {VENV_PYTHON}")
            sys.exit(subprocess.call([VENV_PYTHON] + sys.argv))


def is_port_in_use(port: int = 8000, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def free_port(port: int = 8000):
    """Finds and terminates any process holding the target port on Windows."""
    if not is_port_in_use(port):
        return

    print(f"[MuleGuard] Port {port} is currently in use. Finding occupying process...")
    try:
        # Use netstat to find PID
        cmd = f'netstat -ano | findstr :{port}'
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
        pids = set()
        for line in output.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5 and "LISTENING" in parts:
                pid = parts[-1]
                if pid.isdigit() and int(pid) != os.getpid():
                    pids.add(int(pid))
        
        for pid in pids:
            print(f"[MuleGuard] Terminating lingering process on port {port} (PID: {pid})...")
            try:
                subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"[MuleGuard] Warning: could not terminate PID {pid}: {e}")
        
        # Wait up to 3 seconds for port to clear
        for _ in range(30):
            time.sleep(0.1)
            if not is_port_in_use(port):
                print(f"[MuleGuard] Port {port} successfully cleared.")
                return
    except Exception as e:
        print(f"[MuleGuard] Notice during port clearance: {e}")


def main():
    port = 8000
    host = "127.0.0.1"

    free_port(port)

    # Verify database connection
    try:
        from app.db.database import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        print("[MuleGuard] PostgreSQL database connected successfully.")
    except Exception as e:
        print(f"[MuleGuard] Warning: Database check returned: {e}")
        print("[MuleGuard] Proceeding with server startup...")

    print("=" * 68)
    print("  MuleGuard — Unified Detection & Intelligence Platform")
    print("=" * 68)
    print(f"  * Unified URL:    http://{host}:{port}/")
    print(f"  * Login URL:      http://{host}:{port}/frontend/login.html")
    print(f"  * API Docs:       http://{host}:{port}/docs")
    print("=" * 68)
    print("  Server is running. Press Ctrl+C to stop.\n")

    import uvicorn
    uvicorn.run("app.main:app", host=host, port=port, log_level="info", reload=True)


if __name__ == "__main__":
    main()
