import asyncio
import subprocess
import json
import urllib.request
import websockets

async def test():
    cmd = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        '--remote-debugging-port=9343',
        '--remote-allow-origins=*',
        'about:blank'
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(1.5)
    try:
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9343/json').read())
        pages = [t for t in tabs if t.get('type') == 'page']
        ws_url = pages[0]['webSocketDebuggerUrl']
        async with websockets.connect(ws_url) as ws:
            msg_id = 1
            async def send(method, params=None):
                nonlocal msg_id
                msg_id += 1
                await ws.send(json.dumps({'id': msg_id, 'method': method, 'params': params or {}}))
                while True:
                    res = json.loads(await ws.recv())
                    if res.get('id') == msg_id:
                        return res.get('result', {})

            test_js = """
                (function() {
                    const testSelectors = [
                        '#sidebar-container',
                        'body.sidebar-collapsed #sidebar-container',
                        'div.md\\\\:pl-\\\\[280px\\\\]',
                        'div[class*="md:pl-[280px]"]',
                        'body.sidebar-collapsed div[class*="md:pl-[280px]"]',
                        'body.sidebar-collapsed #sidebar-container, html.sidebar-collapsed #sidebar-container'
                    ];
                    const results = {};
                    for (let sel of testSelectors) {
                        const style = document.createElement('style');
                        document.head.appendChild(style);
                        try {
                            style.sheet.insertRule(sel + ' { width: 72px !important; }', 0);
                            results[sel] = { valid: true, parsed: style.sheet.cssRules[0].cssText };
                        } catch(e) {
                            results[sel] = { valid: false, error: e.message };
                        }
                        style.remove();
                    }
                    return results;
                })()
            """
            res = await send('Runtime.evaluate', {'expression': test_js, 'returnByValue': True})
            print(json.dumps(res.get('result', {}).get('value'), indent=2))
    finally:
        proc.terminate()

asyncio.run(test())
