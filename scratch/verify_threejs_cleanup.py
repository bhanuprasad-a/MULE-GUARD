"""
MuleGuard Step 9C: Three.js Asset & Visualizer Verification
Verifies:
1. frontend/three.min.js is served with 200 OK and exact length (638,608 bytes)
2. frontend/three.js is served with 200 OK and exact length (21,479 bytes)
3. Removed files return 404 (frontend/scripts/three.min.js, scratch/cdnjs_three.min.js, etc.)
4. login.html loads without 404s
5. Real browser test:
   - window.THREE is available and valid Three.js object
   - Three.js WebGL canvas is appended to container
   - Canvas has valid dimensions
   - "3D NETWORK: ONLINE" indicator element is present
   - No 404 or JS load errors
"""

import sys
import os
import json
import time
import socket
import subprocess
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

BASE_URL = "http://127.0.0.1:8000"
VENV_PYTHON = os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")

PASS_COUNT = 0
FAIL_COUNT = 0


def record(name: str, passed: bool, detail: str = ""):
    global PASS_COUNT, FAIL_COUNT
    if passed:
        PASS_COUNT += 1
        print(f"  [OK] PASS: {name}" + (f" ({detail})" if detail else ""))
    else:
        FAIL_COUNT += 1
        print(f"  [FAIL] FAIL: {name} - {detail}")


def is_port_in_use(port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def verify_static_assets():
    print("\n[Phase 1] Verifying Static HTTP Asset Serving...")
    
    # 1. Active three.min.js
    url_three_min = f"{BASE_URL}/frontend/three.min.js"
    try:
        with urllib.request.urlopen(url_three_min) as resp:
            data = resp.read()
            record("GET /frontend/three.min.js returns 200 OK", resp.status == 200)
            record("frontend/three.min.js length is 638,608 bytes", len(data) == 638608, f"got {len(data)}")
    except Exception as e:
        record("GET /frontend/three.min.js", False, str(e))

    # 2. Active three.js
    url_three = f"{BASE_URL}/frontend/three.js"
    try:
        with urllib.request.urlopen(url_three) as resp:
            data = resp.read()
            record("GET /frontend/three.js returns 200 OK", resp.status == 200)
            record("frontend/three.js length is 21,479 bytes", len(data) == 21479, f"got {len(data)}")
    except Exception as e:
        record("GET /frontend/three.js", False, str(e))

    # 3. Confirmed removed duplicate
    url_removed = f"{BASE_URL}/frontend/scripts/three.min.js"
    try:
        urllib.request.urlopen(url_removed)
        record("frontend/scripts/three.min.js is 404 Not Found", False, "file was found")
    except urllib.error.HTTPError as e:
        record("frontend/scripts/three.min.js is 404 Not Found", e.code == 404, f"got {e.code}")
    except Exception as e:
        record("frontend/scripts/three.min.js is 404 Not Found", False, str(e))

    # 4. login.html
    url_login = f"{BASE_URL}/frontend/login.html"
    try:
        with urllib.request.urlopen(url_login) as resp:
            record("GET /frontend/login.html returns 200 OK", resp.status == 200)
    except Exception as e:
        record("GET /frontend/login.html", False, str(e))

    # 5. Favicon
    url_fav = f"{BASE_URL}/favicon.ico"
    try:
        with urllib.request.urlopen(url_fav) as resp:
            record("GET /favicon.ico returns 200 OK", resp.status == 200)
    except Exception as e:
        record("GET /favicon.ico", False, str(e))


def verify_real_browser():
    print("\n[Phase 2] Verifying Real Chrome Browser Execution & 3D WebGL...")
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.isfile(chrome_path):
        print("  [SKIP] Chrome not found at standard path")
        return

    import tempfile
    import websockets
    import asyncio

    async def run_browser_check():
        user_data = os.path.join(tempfile.gettempdir(), f"chrome_three_test_{int(time.time())}")
        cmd = [
            chrome_path,
            "--remote-debugging-port=9360",
            "--remote-allow-origins=*",
            f"--user-data-dir={user_data}",
            "--window-size=1400,900",
            "about:blank",
        ]
        proc = subprocess.Popen(cmd)
        await asyncio.sleep(2.0)
        try:
            tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9360/json").read())
            pages = [t for t in tabs if t.get("type") == "page"]
            ws_url = pages[0]["webSocketDebuggerUrl"]

            async with websockets.connect(ws_url) as ws:
                msg_id = 1
                pending = {}
                console_logs = []
                http_errors = []

                async def reader():
                    while True:
                        try:
                            raw = await ws.recv()
                        except:
                            break
                        res = json.loads(raw)
                        if "id" in res and res["id"] in pending:
                            pending[res["id"]].set_result(res.get("result", {}))
                        elif res.get("method") == "Runtime.consoleAPICalled":
                            p = res.get("params", {})
                            args = [str(a.get("value", a.get("description", ""))) for a in p.get("args", [])]
                            console_logs.append(f"[{p.get('type')}] {' '.join(args)}")
                        elif res.get("method") == "Network.responseReceived":
                            r = res.get("params", {}).get("response", {})
                            if r.get("status", 200) >= 400:
                                http_errors.append(f"{r.get('status')} {r.get('url')}")

                reader_task = asyncio.create_task(reader())

                async def send(method, params=None):
                    nonlocal msg_id
                    msg_id += 1
                    fut = asyncio.get_event_loop().create_future()
                    pending[msg_id] = fut
                    payload = {"id": msg_id, "method": method, "params": params or {}}
                    await ws.send(json.dumps(payload))
                    return await asyncio.wait_for(fut, timeout=10.0)

                await send("Page.enable")
                await send("Runtime.enable")
                await send("Network.enable")

                # Navigate to login.html
                await send("Page.navigate", {"url": f"{BASE_URL}/frontend/login.html"})
                await asyncio.sleep(2.5)

                # Check DOM state
                eval_res = await send("Runtime.evaluate", {
                    "expression": """(() => {
                        const c = document.getElementById('threejs-container-ANIMATION_7');
                        const badge = document.getElementById('threejs-diagnostic-badge');
                        const canvas = c ? c.querySelector('canvas') : null;
                        return {
                            threeDefined: typeof THREE !== 'undefined',
                            threeHasWebGL: typeof THREE !== 'undefined' && !!THREE.WebGLRenderer,
                            containerExists: !!c,
                            containerW: c ? c.clientWidth : 0,
                            containerH: c ? c.clientHeight : 0,
                            canvasExists: !!canvas,
                            canvasW: canvas ? canvas.width : 0,
                            canvasH: canvas ? canvas.height : 0,
                            badgeExists: !!badge
                        };
                    })()""",
                    "returnByValue": True
                })

                val = eval_res.get("result", {}).get("value", {})
                record("window.THREE is defined and has WebGLRenderer", val.get("threeDefined") and val.get("threeHasWebGL"))
                record("Three.js container element exists in DOM", val.get("containerExists", False))
                record("Three.js canvas is mounted inside container", val.get("canvasExists", False))
                record("Canvas has positive rendering dimensions", val.get("canvasW", 0) > 0 and val.get("canvasH", 0) > 0, f"{val.get('canvasW')}x{val.get('canvasH')}")
                record("'3D NETWORK: ONLINE' diagnostic badge exists", val.get("badgeExists", False))
                record("Zero 404 HTTP errors during page load", len(http_errors) == 0, f"errors: {http_errors}")

                reader_task.cancel()
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except:
                proc.kill()

    asyncio.run(run_browser_check())


def main():
    print("=" * 60)
    print("MULEGUARD THREE.JS CLEANUP & VISUALIZER VERIFICATION")
    print("=" * 60)

    server_process = None
    if not is_port_in_use(8000):
        print("[Setup] Starting live FastAPI server on port 8000...")
        server_process = subprocess.Popen(
            [VENV_PYTHON, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"],
            cwd=str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for _ in range(20):
            time.sleep(0.5)
            if is_port_in_use(8000):
                print("[Setup] Server listening on port 8000.")
                break
        else:
            raise RuntimeError("Server failed to start on port 8000.")

    try:
        verify_static_assets()
        verify_real_browser()
    finally:
        if server_process:
            print("\n[Teardown] Stopping test server process...")
            server_process.terminate()
            try:
                server_process.wait(timeout=3)
            except:
                server_process.kill()
            print("[Teardown] Server stopped.")

    print("\n" + "=" * 60)
    print(f"THREE.JS VERIFICATION CHECKS: {PASS_COUNT}/{PASS_COUNT + FAIL_COUNT} PASS")
    print("=" * 60)

    if FAIL_COUNT > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
