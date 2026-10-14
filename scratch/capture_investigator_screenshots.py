import asyncio
import subprocess
import json
import os
import base64
import urllib.request
import websockets

ARTIFACT_DIR = r"C:\Users\Arya\.gemini\antigravity-ide\brain\01b89e0f-0850-4fb6-b0ef-48e518b326bd"
SCRATCH_DIR = os.path.abspath(r"e:\PROJECTS\MULE GUARD\scratch\screenshots")
os.makedirs(SCRATCH_DIR, exist_ok=True)

PAGES = [
    {
        "name": "investigator_dashboard",
        "url": "http://127.0.0.1:8000/frontend/bank/investigator/dashboard.html",
        "title": "Investigator Dashboard"
    },
    {
        "name": "investigator_alerts",
        "url": "http://127.0.0.1:8000/frontend/bank/investigator/alerts.html",
        "title": "Alerts Queue"
    },
    {
        "name": "investigator_cases",
        "url": "http://127.0.0.1:8000/frontend/bank/investigator/cases.html",
        "title": "Case Management"
    },
    {
        "name": "investigator_entities",
        "url": "http://127.0.0.1:8000/frontend/bank/investigator/entities.html",
        "title": "Entity Directory"
    },
    {
        "name": "investigator_network",
        "url": "http://127.0.0.1:8000/frontend/bank/investigator/network-intelligence.html",
        "title": "Network Intelligence"
    },
    {
        "name": "investigator_transactions",
        "url": "http://127.0.0.1:8000/frontend/bank/investigator/transactions.html",
        "title": "Transaction Ledger"
    }
]

async def capture_all():
    import tempfile
    user_data = os.path.join(tempfile.gettempdir(), 'chrome_capt_' + str(int(asyncio.get_event_loop().time())))
    cmd = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        '--remote-debugging-port=9356',
        '--remote-allow-origins=*',
        f'--user-data-dir={user_data}',
        '--window-size=1440,900',
        'about:blank'
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(2.0)
    try:
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9356/json').read())
        pages = [t for t in tabs if t.get('type') == 'page']
        ws_url = pages[0]['webSocketDebuggerUrl']
        async with websockets.connect(ws_url) as ws:
            msg_id = 1
            pending = {}

            async def reader():
                while True:
                    try:
                        raw = await ws.recv()
                    except:
                        break
                    res = json.loads(raw)
                    if 'id' in res and res['id'] in pending:
                        pending[res['id']].set_result(res.get('result', {}))

            reader_task = asyncio.create_task(reader())

            async def send(method, params=None):
                nonlocal msg_id
                msg_id += 1
                fut = asyncio.get_event_loop().create_future()
                pending[msg_id] = fut
                await ws.send(json.dumps({'id': msg_id, 'method': method, 'params': params or {}}))
                return await fut

            await send('Page.enable')
            await send('Runtime.enable')

            # Pre-authenticate session in localStorage/sessionStorage
            # Navigate to login first to set origin context
            await send('Page.navigate', {'url': 'http://127.0.0.1:8000/frontend/login.html'})
            await asyncio.sleep(1.0)

            auth_script = """(() => {
                const sessionObj = {
                    authenticated: true,
                    role: 'bank_investigator',
                    subRole: 'Investigator',
                    email: 'investigator@muleguard.internal',
                    name: 'Senior Fraud Investigator',
                    timestamp: new Date().toISOString()
                };
                sessionStorage.setItem('muleguard_session', JSON.stringify(sessionObj));
                localStorage.setItem('muleguard_session', JSON.stringify(sessionObj));
                return true;
            })()"""
            await send('Runtime.evaluate', {'expression': auth_script, 'returnByValue': True})

            results = []
            for page in PAGES:
                print(f"Navigating to {page['title']} ({page['url']})...")
                await send('Page.navigate', {'url': page['url']})
                # Ensure session is preserved in sessionStorage
                await asyncio.sleep(0.5)
                await send('Runtime.evaluate', {'expression': auth_script, 'returnByValue': True})
                # Wait for data fetching & DOM rendering
                await asyncio.sleep(2.5)

                shot = await send('Page.captureScreenshot', {'format': 'png'})
                if 'data' in shot:
                    img_bytes = base64.b64decode(shot['data'])
                    art_path = os.path.join(ARTIFACT_DIR, f"{page['name']}.png")
                    scratch_path = os.path.join(SCRATCH_DIR, f"{page['name']}.png")
                    with open(art_path, 'wb') as f:
                        f.write(img_bytes)
                    with open(scratch_path, 'wb') as f:
                        f.write(img_bytes)
                    print(f"  [SAVED] {page['name']}.png ({len(img_bytes)} bytes)")
                    results.append({
                        "name": page['name'],
                        "title": page['title'],
                        "artifact_path": art_path,
                        "scratch_path": scratch_path,
                        "size": len(img_bytes)
                    })
                else:
                    print(f"  [FAILED] Failed to capture {page['name']}")

            reader_task.cancel()
            return results
    finally:
        proc.terminate()

if __name__ == '__main__':
    res = asyncio.run(capture_all())
    print("\nSummary:", json.dumps(res, indent=2))
