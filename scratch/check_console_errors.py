import asyncio
import subprocess
import json
import urllib.request
import websockets

async def test():
    cmd = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        '--remote-debugging-port=9346',
        '--remote-allow-origins=*',
        'about:blank'
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(1.5)
    try:
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9346/json').read())
        pages = [t for t in tabs if t.get('type') == 'page']
        ws_url = pages[0]['webSocketDebuggerUrl']
        async with websockets.connect(ws_url) as ws:
            msg_id = 1
            console_errors = []

            async def send(method, params=None):
                nonlocal msg_id
                msg_id += 1
                await ws.send(json.dumps({'id': msg_id, 'method': method, 'params': params or {}}))
                while True:
                    res = json.loads(await ws.recv())
                    if res.get('method') == 'Runtime.consoleAPICalled':
                        p = res.get('params', {})
                        if p.get('type') == 'error':
                            args = [str(a.get('value', '')) for a in p.get('args', [])]
                            console_errors.append(' '.join(args))
                    elif res.get('method') == 'Runtime.exceptionThrown':
                        exc = res.get('params', {}).get('exceptionDetails', {}).get('text', '')
                        console_errors.append(exc)
                    if res.get('id') == msg_id:
                        return res.get('result', {})

            await send('Runtime.enable')
            await send('Page.enable')

            await send('Emulation.setDeviceMetricsOverride', {
                'width': 1400,
                'height': 900,
                'deviceScaleFactor': 1,
                'mobile': False
            })

            # Login
            await send('Page.navigate', {'url': 'http://127.0.0.1:8000/frontend/login.html'})
            await asyncio.sleep(0.5)

            login_js = """
                (async function() {
                    const res1 = await fetch('/api/v1/auth/stage1-login', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ employee_id: 'MG-INV-001', password: 'Password@123' })
                    });
                    const d1 = await res1.json();
                    const resV = await fetch('/api/v1/auth/demo-probe-vector', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ employee_id: 'MG-INV-001', noise_level: 0.0 })
                    });
                    const dV = await resV.json();
                    const res2 = await fetch('/api/v1/auth/stage2-verify-face', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            challenge_token: d1.challenge.challenge_token,
                            probe_vector: dV.probe_vector,
                            liveness_proof: { action_performed: d1.challenge.challenge_action, confidence: 0.98, timestamps: [Date.now()/1000] }
                        })
                    });
                    const d2 = await res2.json();
                    sessionStorage.setItem('muleguard_session', JSON.stringify({
                        authenticated: true,
                        role: d2.user.role,
                        user: d2.user
                    }));
                    return true;
                })()
            """
            await send('Runtime.evaluate', {'expression': login_js, 'awaitPromise': True})

            test_targets = [
                'dashboard.html',
                'alerts.html',
                'risk-analytics.html',
                'network-intelligence.html',
                'watchlists.html'
            ]

            results = {}

            for page in test_targets:
                console_errors.clear()
                url = f'http://127.0.0.1:8000/frontend/bank/investigator/{page}'
                await send('Page.navigate', {'url': url})
                await asyncio.sleep(1.2)

                # Click toggle twice
                toggle_js = """
                    (async function() {
                        const toggleBtn = document.getElementById('sidebar-toggle-btn');
                        if (toggleBtn) {
                            toggleBtn.click();
                            await new Promise(r => setTimeout(r, 250));
                            toggleBtn.click();
                            await new Promise(r => setTimeout(r, 250));
                        }
                    })()
                """
                await send('Runtime.evaluate', {'expression': toggle_js, 'awaitPromise': True})
                await asyncio.sleep(0.5)

                sidebar_errors = [e for e in console_errors if 'sidebar' in e.lower() or 'toggle' in e.lower() or 'auth-guard' in e.lower()]
                results[page] = {
                    'total_console_errors': len(console_errors),
                    'sidebar_errors': sidebar_errors,
                    'all_errors': console_errors[:]
                }

            print(json.dumps(results, indent=2))
    finally:
        proc.terminate()

asyncio.run(test())
