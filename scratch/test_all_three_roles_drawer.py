import asyncio
import subprocess
import json
import urllib.request
import websockets

ROLES_TO_TEST = [
    {
        'role_name': 'Investigator',
        'employee_id': 'MG-INV-001',
        'expected_name': 'J. Doe',
        'expected_role_label': 'FRAUD INVESTIGATOR',
        'expected_dept': 'Fraud Investigations',
        'dashboard_url': 'http://127.0.0.1:8000/frontend/bank/investigator/dashboard.html',
        'expected_role_setting_substring': 'Case Assignment'
    },
    {
        'role_name': 'Compliance Officer',
        'employee_id': 'MG-CMP-001',
        'expected_name': 'A. Kumar',
        'expected_role_label': 'COMPLIANCE OFFICER',
        'expected_dept': 'AML Compliance',
        'dashboard_url': 'http://127.0.0.1:8000/frontend/bank/compliance/dashboard.html',
        'expected_role_setting_substring': 'Regulatory Filing'
    },
    {
        'role_name': 'Platform Administrator (Internal Team)',
        'employee_id': 'MG-ADM-001',
        'expected_name': 'T. Miller',
        'expected_role_label': 'PLATFORM ADMIN',
        'expected_dept': 'Core Platform Engineering',
        'dashboard_url': 'http://127.0.0.1:8000/frontend/internal/dashboard.html',
        'expected_role_setting_substring': 'System Node'
    }
]

async def run_tests():
    cmd = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        '--remote-debugging-port=9350',
        '--remote-allow-origins=*',
        'about:blank'
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(1.5)
    try:
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9350/json').read())
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

            results = {}

            for role_cfg in ROLES_TO_TEST:
                role_name = role_cfg['role_name']
                emp_id = role_cfg['employee_id']
                print(f"\n{'='*60}\nTESTING ROLE: {role_name} ({emp_id})\n{'='*60}")

                # 1. Login
                await send('Page.navigate', {'url': 'http://127.0.0.1:8000/frontend/login.html'})
                await asyncio.sleep(0.5)

                login_js = f"""
                    (async function() {{
                        const res1 = await fetch('/api/v1/auth/stage1-login', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{ employee_id: '{emp_id}', password: 'Password@123' }})
                        }});
                        const d1 = await res1.json();
                        const resV = await fetch('/api/v1/auth/demo-probe-vector', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{ employee_id: '{emp_id}', noise_level: 0.0 }})
                        }});
                        const dV = await resV.json();
                        const res2 = await fetch('/api/v1/auth/stage2-verify-face', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{
                                challenge_token: d1.challenge.challenge_token,
                                probe_vector: dV.probe_vector,
                                liveness_proof: {{ action_performed: d1.challenge.challenge_action, confidence: 0.98, timestamps: [Date.now()/1000] }}
                            }})
                        }});
                        const d2 = await res2.json();
                        sessionStorage.setItem('muleguard_session', JSON.stringify({{
                            authenticated: true,
                            role: d2.user.role,
                            user: d2.user
                        }}));
                        return d2.redirect_url;
                    }})()
                """
                redirect_url = (await send('Runtime.evaluate', {'expression': login_js, 'awaitPromise': True, 'returnByValue': True})).get('result', {}).get('value')
                print(f"Logged in as {emp_id}, redirect: {redirect_url}")

                # 2. Navigate to Dashboard
                await send('Page.navigate', {'url': role_cfg['dashboard_url']})
                await asyncio.sleep(1.5)

                test_role_js = f"""
                    (async function() {{
                        const initialUrl = window.location.href;
                        
                        // Check if drawer exists
                        const drawer = document.getElementById('muleguard-profile-drawer');
                        const overlay = document.getElementById('muleguard-profile-drawer-overlay');
                        
                        // 1. Open Profile via window.openProfileDrawer('profile')
                        window.openProfileDrawer('profile');
                        await new Promise(r => setTimeout(r, 350));
                        
                        const isDrawerOpen = drawer && drawer.classList.contains('translate-x-0');
                        const isOverlayOpen = overlay && overlay.classList.contains('opacity-100');
                        
                        // Read profile fields
                        const displayedName = document.getElementById('drawer-profile-name') ? document.getElementById('drawer-profile-name').textContent.trim() : null;
                        const displayedEmpId = document.getElementById('drawer-profile-empid') ? document.getElementById('drawer-profile-empid').textContent.trim() : null;
                        const displayedDept = document.getElementById('drawer-detail-dept') ? document.getElementById('drawer-detail-dept').textContent.trim() : null;
                        const displayedEmail = document.getElementById('drawer-detail-email') ? document.getElementById('drawer-detail-email').textContent.trim() : null;
                        const displayedFace = document.getElementById('drawer-detail-face') ? document.getElementById('drawer-detail-face').textContent.trim() : null;
                        
                        // 2. Switch to Settings tab
                        window.switchDrawerTab('settings');
                        await new Promise(r => setTimeout(r, 100));
                        
                        const isSettingsTabActive = !document.getElementById('drawer-tab-settings-content').classList.contains('hidden');
                        const roleSettingsLabel = document.getElementById('role-settings-label') ? document.getElementById('role-settings-label').textContent.trim() : null;
                        const roleSettingsHtml = document.getElementById('role-settings-container') ? document.getElementById('role-settings-container').innerText : '';
                        
                        // 3. Test Theme Setting
                        window.setMuleGuardTheme('dark');
                        const isDarkMode = document.documentElement.classList.contains('dark');
                        window.setMuleGuardTheme('light');
                        const isLightMode = document.documentElement.classList.contains('light');
                        
                        // 4. Test Density Setting
                        window.setMuleGuardDensity('compact');
                        const isCompact = document.documentElement.classList.contains('density-compact');
                        window.setMuleGuardDensity('comfortable');
                        const isComfortable = !document.documentElement.classList.contains('density-compact');
                        
                        // 5. Test Close with ESC
                        window.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Escape' }}));
                        await new Promise(r => setTimeout(r, 350));
                        const isClosedViaEsc = drawer.classList.contains('translate-x-full');
                        
                        // 6. Test Re-open & Close via X button
                        window.openProfileDrawer('profile');
                        await new Promise(r => setTimeout(r, 350));
                        const closeBtn = drawer.querySelector('button[title*="Close"]');
                        if (closeBtn) closeBtn.click();
                        await new Promise(r => setTimeout(r, 350));
                        const isClosedViaBtn = drawer.classList.contains('translate-x-full');
                        
                        // 7. Test Re-open & Close via Outside Overlay Click
                        window.openProfileDrawer('profile');
                        await new Promise(r => setTimeout(r, 350));
                        overlay.click();
                        await new Promise(r => setTimeout(r, 350));
                        const isClosedViaOverlay = drawer.classList.contains('translate-x-full');
                        
                        const finalUrl = window.location.href;
                        const noPageNavOccurred = (initialUrl === finalUrl);
                        
                        return {{
                            initialUrl,
                            isDrawerOpen,
                            isOverlayOpen,
                            displayedName,
                            displayedEmpId,
                            displayedDept,
                            displayedEmail,
                            displayedFace,
                            isSettingsTabActive,
                            roleSettingsLabel,
                            hasExpectedRoleSettings: roleSettingsHtml.includes('{role_cfg["expected_role_setting_substring"]}'),
                            isDarkModeWorks: isDarkMode,
                            isLightModeWorks: isLightMode,
                            isCompactWorks: isCompact,
                            isComfortableWorks: isComfortable,
                            isClosedViaEsc,
                            isClosedViaBtn,
                            isClosedViaOverlay,
                            noPageNavOccurred
                        }};
                    }})()
                """
                test_res = (await send('Runtime.evaluate', {'expression': test_role_js, 'awaitPromise': True, 'returnByValue': True})).get('result', {}).get('value')
                results[role_name] = test_res
                print(json.dumps(test_res, indent=2))

            print("\n" + "="*60 + "\nOVERALL TEST SUMMARY\n" + "="*60)
            print(json.dumps(results, indent=2))
    finally:
        proc.terminate()

asyncio.run(run_tests())
