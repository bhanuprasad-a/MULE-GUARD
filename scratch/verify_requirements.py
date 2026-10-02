import asyncio
import subprocess
import json
import urllib.request
import websockets

async def test():
    cmd = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        '--remote-debugging-port=9345',
        '--remote-allow-origins=*',
        'about:blank'
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(1.5)
    try:
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9345/json').read())
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

            await send('Emulation.setDeviceMetricsOverride', {
                'width': 1400,
                'height': 900,
                'deviceScaleFactor': 1,
                'mobile': False
            })

            await send('Page.navigate', {'url': 'http://127.0.0.1:8000/frontend/login.html'})
            await asyncio.sleep(0.5)

            # Login
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
                url = f'http://127.0.0.1:8000/frontend/bank/investigator/{page}'
                await send('Page.navigate', {'url': url})
                await asyncio.sleep(1.2)

                # 1. Check initial state
                inspect_initial = """
                    (function() {
                        const s = document.getElementById('sidebar-container');
                        const toggleBtn = document.getElementById('sidebar-toggle-btn');
                        const mainLayout = document.querySelector('div[class*="md:pl-[280px]"], #main-content-layout');
                        const links = Array.from(document.querySelectorAll('#sidebar-container a.nav-item-link')).map(a => ({
                            id: a.id,
                            href: a.getAttribute('href'),
                            text: a.querySelector('.sidebar-text') ? a.querySelector('.sidebar-text').textContent.trim() : a.textContent.trim(),
                            isActive: a.classList.contains('bg-secondary-container/25') && !a.classList.contains('border-transparent')
                        }));
                        const active = links.find(l => l.isActive);
                        return {
                            hasSidebar: !!s,
                            hasToggleBtn: !!toggleBtn,
                            width: s ? s.offsetWidth : 0,
                            padding: mainLayout ? window.getComputedStyle(mainLayout).paddingLeft : null,
                            activeLink: active ? active.text : null,
                            linksCount: links.length
                        };
                    })()
                """
                init_res = (await send('Runtime.evaluate', {'expression': inspect_initial, 'returnByValue': True})).get('result', {}).get('value')

                # 2. Toggle to collapsed
                toggle_collapse = """
                    (async function() {
                        const toggleBtn = document.getElementById('sidebar-toggle-btn');
                        if (toggleBtn) toggleBtn.click();
                        await new Promise(r => setTimeout(r, 350));
                        const s = document.getElementById('sidebar-container');
                        const mainLayout = document.querySelector('div[class*="md:pl-[280px]"], #main-content-layout');
                        const icon = document.getElementById('sidebar-toggle-icon');
                        return {
                            isCollapsed: document.body.classList.contains('sidebar-collapsed'),
                            width: s ? s.offsetWidth : 0,
                            padding: mainLayout ? window.getComputedStyle(mainLayout).paddingLeft : null,
                            icon: icon ? icon.textContent.trim() : null,
                            localStorage: localStorage.getItem('muleguard_sidebar_collapsed')
                        };
                    })()
                """
                col_res = (await send('Runtime.evaluate', {'expression': toggle_collapse, 'awaitPromise': True, 'returnByValue': True})).get('result', {}).get('value')

                # 3. Reload page while collapsed and verify persistence
                await send('Page.reload')
                await asyncio.sleep(1.2)

                reload_check = """
                    (function() {
                        const s = document.getElementById('sidebar-container');
                        const mainLayout = document.querySelector('div[class*="md:pl-[280px]"], #main-content-layout');
                        const icon = document.getElementById('sidebar-toggle-icon');
                        return {
                            isCollapsed: document.body.classList.contains('sidebar-collapsed'),
                            width: s ? s.offsetWidth : 0,
                            padding: mainLayout ? window.getComputedStyle(mainLayout).paddingLeft : null,
                            icon: icon ? icon.textContent.trim() : null
                        };
                    })()
                """
                reload_res = (await send('Runtime.evaluate', {'expression': reload_check, 'returnByValue': True})).get('result', {}).get('value')

                # 4. Toggle back to expanded
                toggle_expand = """
                    (async function() {
                        const toggleBtn = document.getElementById('sidebar-toggle-btn');
                        if (toggleBtn) toggleBtn.click();
                        await new Promise(r => setTimeout(r, 350));
                        const s = document.getElementById('sidebar-container');
                        const mainLayout = document.querySelector('div[class*="md:pl-[280px]"], #main-content-layout');
                        const icon = document.getElementById('sidebar-toggle-icon');
                        return {
                            isCollapsed: document.body.classList.contains('sidebar-collapsed'),
                            width: s ? s.offsetWidth : 0,
                            padding: mainLayout ? window.getComputedStyle(mainLayout).paddingLeft : null,
                            icon: icon ? icon.textContent.trim() : null,
                            localStorage: localStorage.getItem('muleguard_sidebar_collapsed')
                        };
                    })()
                """
                exp_res = (await send('Runtime.evaluate', {'expression': toggle_expand, 'awaitPromise': True, 'returnByValue': True})).get('result', {}).get('value')

                results[page] = {
                    'initial': init_res,
                    'collapsed': col_res,
                    'after_reload': reload_res,
                    'expanded': exp_res
                }

            print(json.dumps(results, indent=2))
    finally:
        proc.terminate()

asyncio.run(test())
