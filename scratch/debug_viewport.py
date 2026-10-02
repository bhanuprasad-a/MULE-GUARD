import asyncio
import subprocess
import json
import urllib.request
import websockets

async def test():
    cmd = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        '--remote-debugging-port=9341',
        '--remote-allow-origins=*',
        'about:blank'
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(1.5)
    try:
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9341/json').read())
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

            pages = [
                'dashboard.html',
                'alerts.html',
                'risk-analytics.html',
                'network-intelligence.html',
                'watchlists.html'
            ]

            results = {}

            for page in pages:
                url = f'http://127.0.0.1:8000/frontend/bank/investigator/{page}'
                await send('Page.navigate', {'url': url})
                await asyncio.sleep(1.5)

                inspect_js = """
                    (async function() {
                        try {
                            const s = document.getElementById('sidebar-container');
                            const toggleBtn = document.getElementById('sidebar-toggle-btn');
                            const mainLayout = document.querySelector('div[class*="md:pl-[280px]"], #main-content-layout');
                            
                            const initialWidth = s ? s.offsetWidth : 0;
                            const initialPadding = mainLayout ? window.getComputedStyle(mainLayout).paddingLeft : null;
                            
                            const links = Array.from(document.querySelectorAll('#sidebar-container a.nav-item-link')).map(a => ({
                                id: a.id,
                                href: a.getAttribute('href'),
                                text: a.querySelector('.sidebar-text') ? a.querySelector('.sidebar-text').textContent.trim() : a.textContent.trim(),
                                isActive: a.classList.contains('bg-secondary-container/25') && !a.classList.contains('border-transparent')
                            }));
                            const activeLink = links.find(l => l.isActive);
                            
                            if (toggleBtn) toggleBtn.click();
                            await new Promise(r => setTimeout(r, 350));
                            
                            const collapsedWidth = s ? s.offsetWidth : 0;
                            const collapsedPadding = mainLayout ? window.getComputedStyle(mainLayout).paddingLeft : null;
                            const iconCollapsed = document.getElementById('sidebar-toggle-icon') ? document.getElementById('sidebar-toggle-icon').textContent.trim() : null;
                            
                            if (toggleBtn) toggleBtn.click();
                            await new Promise(r => setTimeout(r, 350));
                            
                            const expandedWidth = s ? s.offsetWidth : 0;
                            const expandedPadding = mainLayout ? window.getComputedStyle(mainLayout).paddingLeft : null;
                            const iconExpanded = document.getElementById('sidebar-toggle-icon') ? document.getElementById('sidebar-toggle-icon').textContent.trim() : null;
                            
                            return {
                                pageUrl: window.location.href,
                                hasSidebar: !!s,
                                hasToggleBtn: !!toggleBtn,
                                activeLink: activeLink ? activeLink.text : null,
                                linksCount: links.length,
                                initialWidth,
                                initialPadding,
                                collapsedWidth,
                                collapsedPadding,
                                iconCollapsed,
                                expandedWidth,
                                expandedPadding,
                                iconExpanded
                            };
                        } catch(err) {
                            return { error: err.message, stack: err.stack };
                        }
                    })()
                """
                res = await send('Runtime.evaluate', {'expression': inspect_js, 'awaitPromise': True, 'returnByValue': True})
                results[page] = res.get('result', {}).get('value')

            print(json.dumps(results, indent=2))
    finally:
        proc.terminate()

asyncio.run(test())
