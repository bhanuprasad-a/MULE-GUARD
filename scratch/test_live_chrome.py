import asyncio
import subprocess
import json
import urllib.request
import os
import websockets

CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
PORT = 9333
USER_DATA_DIR = os.path.join(os.environ['TEMP'], 'chrome_test_investigator_sidebar')

PAGES = [
    'http://127.0.0.1:8000/frontend/bank/investigator/dashboard.html',
    'http://127.0.0.1:8000/frontend/bank/investigator/alerts.html',
    'http://127.0.0.1:8000/frontend/bank/investigator/risk-analytics.html',
    'http://127.0.0.1:8000/frontend/bank/investigator/network-intelligence.html',
    'http://127.0.0.1:8000/frontend/bank/investigator/watchlists.html'
]

async def cdp_send(ws, method, params=None, msg_id=1):
    payload = {'id': msg_id, 'method': method, 'params': params or {}}
    await ws.send(json.dumps(payload))
    while True:
        res = json.loads(await ws.recv())
        if res.get('id') == msg_id:
            return res.get('result', {})

async def evaluate_js(ws, expr, msg_id=100):
    res = await cdp_send(ws, 'Runtime.evaluate', {
        'expression': expr,
        'returnByValue': True,
        'awaitPromise': True
    }, msg_id)
    return res.get('result', {}).get('value')

async def run_tests():
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
        page_tab = [t for t in tabs if t.get('type') == 'page'][0]
        ws_url = page_tab['webSocketDebuggerUrl']

        async with websockets.connect(ws_url) as ws:
            await cdp_send(ws, 'Page.enable', {}, 1)
            await cdp_send(ws, 'Runtime.enable', {}, 2)

            msg_id = 10

            # 1. Navigate to login.html and perform real authentication
            print("\n[STEP 1] Logging in as MG-INV-001...")
            await cdp_send(ws, 'Page.navigate', {'url': 'http://127.0.0.1:8000/frontend/login.html'}, msg_id)
            msg_id += 1
            await asyncio.sleep(1.5)

            login_js = """
                (async function() {
                    const res1 = await fetch('/api/v1/auth/stage1-login', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ employee_id: 'MG-INV-001', password: 'Password@123' })
                    });
                    const data1 = await res1.json();
                    if (!res1.ok) return { error: data1.detail || 'Stage 1 failed' };

                    const resVec = await fetch('/api/v1/auth/demo-probe-vector', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ employee_id: 'MG-INV-001', noise_level: 0.0 })
                    });
                    const dataVec = await resVec.json();

                    const res2 = await fetch('/api/v1/auth/stage2-verify-face', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            challenge_token: data1.challenge.challenge_token,
                            probe_vector: dataVec.probe_vector,
                            liveness_proof: {
                                action_performed: data1.challenge.challenge_action,
                                confidence: 0.98,
                                timestamps: [Date.now()/1000]
                            }
                        })
                    });
                    const data2 = await res2.json();
                    if (!res2.ok) return { error: data2.detail || 'Stage 2 failed' };

                    const session = {
                        authenticated: true,
                        role: data2.user.role,
                        user: {
                            id: data2.user.id,
                            employee_id: data2.user.employee_id,
                            name: data2.user.name,
                            title: data2.user.title,
                            email: data2.user.email
                        }
                    };
                    sessionStorage.setItem('muleguard_session', JSON.stringify(session));
                    return { success: true, redirect_url: data2.redirect_url, session: session };
                })()
            """
            login_result = await evaluate_js(ws, login_js, msg_id)
            msg_id += 1
            print("Login Result:", json.dumps(login_result, indent=2))

            # 2. Test each of the 5 pages
            for page_url in PAGES:
                page_name = page_url.split('/')[-1]
                print(f'\n{"="*60}\nTESTING: {page_name}\n{"="*60}')

                await cdp_send(ws, 'Page.navigate', {'url': page_url}, msg_id)
                msg_id += 1
                await asyncio.sleep(1.2)

                curr_url = await evaluate_js(ws, 'window.location.href', msg_id)
                msg_id += 1
                print(f'Current URL: {curr_url}')

                # Extract console errors
                err_check = await evaluate_js(ws, """
                    (function() {
                        const s = document.getElementById('sidebar-container');
                        if (!s) return { sidebarFound: false, html: document.body.innerHTML.substring(0, 300) };
                        const toggleBtn = document.getElementById('sidebar-toggle-btn');
                        const toggleIcon = document.getElementById('sidebar-toggle-icon');
                        const links = Array.from(s.querySelectorAll('a.nav-item-link')).map(a => ({
                            id: a.id,
                            href: a.getAttribute('href'),
                            label: a.querySelector('.sidebar-text') ? a.querySelector('.sidebar-text').textContent.trim() : a.textContent.trim(),
                            isActive: a.classList.contains('bg-secondary-container/25') || a.className.includes('bg-secondary-container')
                        }));
                        const activeItem = links.find(l => l.isActive);
                        return {
                            sidebarFound: true,
                            width: s.offsetWidth,
                            hasToggleBtn: !!toggleBtn,
                            toggleIcon: toggleIcon ? toggleIcon.textContent.trim() : null,
                            linksCount: links.length,
                            activeItem: activeItem,
                            allLinks: links.map(l => (l.isActive ? '* ' : '  ') + l.label + ' (' + l.href + ')')
                        };
                    })()
                """, msg_id)
                msg_id += 1
                print("Sidebar State:", json.dumps(err_check, indent=2))

                # Test toggle functionality
                if err_check.get('hasToggleBtn'):
                    toggle_test = await evaluate_js(ws, """
                        (function() {
                            const btn = document.getElementById('sidebar-toggle-btn');
                            const s = document.getElementById('sidebar-container');
                            const toggleIcon = document.getElementById('sidebar-toggle-icon');
                            const mainLayout = document.querySelector('div.md\\\\:pl-\\\\[280px\\\\], main.md\\\\:pl-\\\\[280px\\\\], #main-content-layout');
                            const initialWidth = s.offsetWidth;

                            // 1. Collapse
                            btn.click();
                            const collapsedWidth = s.offsetWidth;
                            const isCollapsed = document.body.classList.contains('sidebar-collapsed');
                            const iconCollapsed = toggleIcon ? toggleIcon.textContent.trim() : null;
                            const mainPaddingCollapsed = mainLayout ? window.getComputedStyle(mainLayout).paddingLeft : null;

                            // 2. Expand
                            btn.click();
                            const expandedWidth = s.offsetWidth;
                            const isExpanded = !document.body.classList.contains('sidebar-collapsed');
                            const iconExpanded = toggleIcon ? toggleIcon.textContent.trim() : null;
                            const mainPaddingExpanded = mainLayout ? window.getComputedStyle(mainLayout).paddingLeft : null;

                            return {
                                initialWidth: initialWidth,
                                collapsedWidth: collapsedWidth,
                                isCollapsed: isCollapsed,
                                iconCollapsed: iconCollapsed,
                                mainPaddingCollapsed: mainPaddingCollapsed,
                                expandedWidth: expandedWidth,
                                isExpanded: isExpanded,
                                iconExpanded: iconExpanded,
                                mainPaddingExpanded: mainPaddingExpanded
                            };
                        })()
                    """, msg_id)
                    msg_id += 1
                    print("Toggle Test Result:", json.dumps(toggle_test, indent=2))
                else:
                    print("ERROR: Toggle button not found!")

    finally:
        proc.terminate()

asyncio.run(run_tests())
