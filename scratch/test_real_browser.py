import asyncio
import subprocess
import json
import urllib.request
import websockets

async def test():
    # Launch Chrome as a real user browser (not headless) with debugging port
    import tempfile, os
    user_data = os.path.join(tempfile.gettempdir(), 'chrome_real_' + str(int(asyncio.get_event_loop().time())))
    cmd = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--remote-debugging-port=9355',
        '--remote-allow-origins=*',
        f'--user-data-dir={user_data}',
        '--window-size=1400,900',
        'about:blank'
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(2.0)
    try:
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9355/json').read())
        pages = [t for t in tabs if t.get('type') == 'page']
        ws_url = pages[0]['webSocketDebuggerUrl']
        async with websockets.connect(ws_url) as ws:
            msg_id = 1
            pending = {}
            console_logs = []

            async def reader():
                while True:
                    try:
                        raw = await ws.recv()
                    except:
                        break
                    res = json.loads(raw)
                    if 'id' in res and res['id'] in pending:
                        pending[res['id']].set_result(res.get('result', {}))
                    elif res.get('method') == 'Runtime.consoleAPICalled':
                        p = res.get('params', {})
                        args = [str(a.get('value', a.get('description', ''))) for a in p.get('args', [])]
                        console_logs.append(f"[{p.get('type')}] {' '.join(args)}")
                    elif res.get('method') == 'Runtime.exceptionThrown':
                        exc = res.get('params', {}).get('exceptionDetails', {}).get('text', '')
                        desc = res.get('params', {}).get('exceptionDetails', {}).get('exception', {}).get('description', '')
                        console_logs.append(f"[EXCEPTION] {exc} {desc}")
                    elif res.get('method') == 'Network.responseReceived':
                        resp = res.get('params', {}).get('response', {})
                        if resp.get('status', 200) >= 400:
                            console_logs.append(f"[HTTP {resp.get('status')}] {resp.get('url')}")
                    elif res.get('method') == 'Log.entryAdded':
                        entry = res.get('params', {}).get('entry', {})
                        console_logs.append(f"[LOG {entry.get('level')}] {entry.get('text')}")

            reader_task = asyncio.create_task(reader())

            async def send(method, params=None):
                nonlocal msg_id
                msg_id += 1
                fut = asyncio.get_event_loop().create_future()
                pending[msg_id] = fut
                await ws.send(json.dumps({'id': msg_id, 'method': method, 'params': params or {}}))
                return await fut

            await send('Runtime.enable')
            await send('Page.enable')
            await send('Log.enable')
            await send('Network.enable')

            print("Navigating to http://127.0.0.1:8000/frontend/login.html...")
            await send('Page.navigate', {'url': 'http://127.0.0.1:8000/frontend/login.html'})
            await asyncio.sleep(2.0)

            # Check what's in the DOM
            eval_res = await send('Runtime.evaluate', {
                'expression': """(() => {
                    const c = document.getElementById('threejs-container-ANIMATION_7');
                    const badge = document.getElementById('threejs-diagnostic-badge');
                    const canvas = c ? c.querySelector('canvas') : null;
                    return {
                        readyState: document.readyState,
                        threeDefined: typeof THREE !== 'undefined',
                        threeHasWebGL: typeof THREE !== 'undefined' && !!THREE.WebGLRenderer,
                        containerExists: !!c,
                        containerW: c ? c.clientWidth : null,
                        containerH: c ? c.clientHeight : null,
                        canvasExists: !!canvas,
                        canvasW: canvas ? canvas.width : null,
                        canvasH: canvas ? canvas.height : null,
                        badgeExists: !!badge
                    };
                })()""",
                'returnByValue': True
            })

            print("DOM State in real browser:")
            val = eval_res.get('result', {}).get('value') if 'result' in eval_res else eval_res.get('value')
            print(json.dumps(val or eval_res, indent=2))
            print("Console logs:")
            for log in console_logs:
                print(log)

            # Take screenshot
            import base64
            screenshot = await send('Page.captureScreenshot', {'format': 'png'})
            if 'data' in screenshot:
                with open('scratch/real_browser_screenshot.png', 'wb') as f:
                    f.write(base64.b64decode(screenshot['data']))
                print("Screenshot saved to scratch/real_browser_screenshot.png")

            reader_task.cancel()
    finally:
        proc.terminate()

asyncio.run(test())
