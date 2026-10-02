import asyncio, subprocess, json, urllib.request, os, websockets

CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
PORT = 9334
USER_DATA_DIR = os.path.join(os.environ['TEMP'], 'chrome_test_css_9334')

async def run():
    cmd = [
        CHROME_PATH,
        '--headless=new',
        f'--remote-debugging-port={PORT}',
        '--remote-allow-origins=*',
        f'--user-data-dir={USER_DATA_DIR}',
        '--disable-gpu',
        'about:blank'
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(2)
    try:
        tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json').read())
        ws_url = tabs[0]['webSocketDebuggerUrl']
        async with websockets.connect(ws_url) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {
                'expression': """
                    (function() {
                        const style = document.createElement('style');
                        style.id = 'test-style';
                        style.textContent = `
                            body.sidebar-collapsed #sidebar-container { width: 72px !important; }
                        `;
                        document.head.appendChild(style);
                        const s = document.createElement('aside');
                        s.id = 'sidebar-container';
                        s.className = 'w-[280px]';
                        document.body.appendChild(s);
                        document.body.classList.add('sidebar-collapsed');
                        return {
                            appliedWidth: window.getComputedStyle(s).width,
                            sheetRules: Array.from(style.sheet.cssRules).map(r => r.cssText)
                        };
                    })()
                """,
                'returnByValue': True
            }}))
            res = json.loads(await ws.recv())
            print(res['result']['result']['value'])
    finally:
        proc.terminate()

asyncio.run(run())
