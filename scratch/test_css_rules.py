import asyncio, subprocess, json, urllib.request, os, websockets

CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
PORT = 9335
USER_DATA_DIR = os.path.join(os.environ['TEMP'], 'chrome_test_css_9335')

async def run():
    cmd = [
        CHROME_PATH,
        '--headless=new',
        f'--remote-debugging-port={PORT}',
        '--remote-allow-origins=*',
        f'--user-data-dir={USER_DATA_DIR}',
        '--disable-gpu',
        '--window-size=1400,900',
        'about:blank'
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(2)
    try:
        tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json').read())
        ws_url = tabs[0]['webSocketDebuggerUrl']
        async with websockets.connect(ws_url) as ws:
            with open('frontend/scripts/auth-guard.js', 'r', encoding='utf-8') as f:
                code = f.read()

            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {
                'expression': f"""
                    (function() {{
                        // Execute auth-guard
                        {code}
                        const s = document.createElement('aside');
                        s.id = 'sidebar-container';
                        s.className = 'w-[280px]';
                        document.body.appendChild(s);
                        document.body.classList.add('sidebar-collapsed');

                        const styleEl = document.getElementById('muleguard-collapsible-sidebar-css');
                        const rules = styleEl && styleEl.sheet ? Array.from(styleEl.sheet.cssRules).map(r => r.cssText) : [];

                        return {{
                            computedWidth: window.getComputedStyle(s).width,
                            styleExists: !!styleEl,
                            ruleCount: rules.length,
                            rules: rules
                        }};
                    }})()
                """,
                'returnByValue': True
            }}))
            res = json.loads(await ws.recv())
            print(json.dumps(res['result']['result']['value'], indent=2))
    finally:
        proc.terminate()

asyncio.run(run())
