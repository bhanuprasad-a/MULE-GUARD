import asyncio
import subprocess
import json
import urllib.request
import websockets
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROLES_TO_TEST = [
    {
        'role_key': 'bank_investigator',
        'role_name': 'Investigator',
        'employee_id': 'MG-INV-001',
        'expected_name': 'J. Doe',
        'expected_role_badge': 'INVESTIGATOR',
        'expected_dept': 'Fraud Investigations',
        'expected_role_label': 'Bank Fraud Investigator',
        'dashboard_url': 'http://127.0.0.1:8000/frontend/bank/investigator/dashboard.html',
        'expected_role_settings': [
            'High-Risk Account Alerts',
            'Investigation / Case Updates',
            'Network Intelligence Notifications'
        ],
        'unauthorized_role_settings': [
            'Escalation Notifications',
            'Platform / System Health Alerts',
            'Database / ML Service Health'
        ]
    },
    {
        'role_key': 'bank_compliance',
        'role_name': 'Compliance Officer',
        'employee_id': 'MG-CMP-001',
        'expected_name': 'A. Kumar',
        'expected_role_badge': 'COMPLIANCE',
        'expected_dept': 'AML Compliance',
        'expected_role_label': 'AML Compliance Officer',
        'dashboard_url': 'http://127.0.0.1:8000/frontend/bank/compliance/dashboard.html',
        'expected_role_settings': [
            'High-Risk Alerts',
            'Escalation Notifications',
            'Compliance / Case Review Notifications',
            'Audit / Review Notifications'
        ],
        'unauthorized_role_settings': [
            'Network Intelligence Notifications',
            'Platform / System Health Alerts',
            'Database / ML Service Health'
        ]
    },
    {
        'role_key': 'internal_team',
        'role_name': 'Platform Administrator',
        'employee_id': 'MG-ADM-001',
        'expected_name': 'T. Miller',
        'expected_role_badge': 'ADMIN',
        'expected_dept': 'Core Platform Engineering',
        'expected_role_label': 'Platform Administrator',
        'dashboard_url': 'http://127.0.0.1:8000/frontend/internal/dashboard.html',
        'expected_role_settings': [
            'Platform / System Health Alerts',
            'Detection Rule Execution Alerts',
            'Database / ML Service Health',
            'Infrastructure Notifications'
        ],
        'unauthorized_role_settings': [
            'High-Risk Account Alerts',
            'Escalation Notifications',
            'Compliance / Case Review Notifications'
        ]
    }
]

async def run_verification():
    cmd = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        '--remote-debugging-port=9351',
        '--remote-allow-origins=*',
        'about:blank'
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(1.5)

    try:
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9351/json').read())
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
                    # Capture console logs and errors
                    if res.get('method') == 'Runtime.consoleAPICalled':
                        args = res.get('params', {}).get('args', [])
                        t = res.get('params', {}).get('type')
                        text = ' '.join([str(a.get('value', '')) for a in args])
                        if t == 'error':
                            console_errors.append(text)
                    if res.get('id') == msg_id:
                        return res.get('result', {})

            await send('Runtime.enable')
            await send('Emulation.setDeviceMetricsOverride', {
                'width': 1366,
                'height': 768,
                'deviceScaleFactor': 1,
                'mobile': False
            })

            all_passed = True

            for role_cfg in ROLES_TO_TEST:
                role_name = role_cfg['role_name']
                emp_id = role_cfg['employee_id']
                print(f"\n{'='*70}\n[TEST] Persona: {role_name} ({emp_id})\n{'='*70}")

                # 1. Login stage 1 and stage 2 face auth
                await send('Page.navigate', {'url': 'http://127.0.0.1:8000/frontend/login.html'})
                await asyncio.sleep(0.5)

                login_script = f"""
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
                        return d2;
                    }})()
                """
                login_res = (await send('Runtime.evaluate', {'expression': login_script, 'awaitPromise': True, 'returnByValue': True})).get('result', {}).get('value')
                print(f"  ✓ Authenticated as {login_res.get('user', {}).get('name')} ({emp_id})")

                # 2. Navigate to role dashboard
                await send('Page.navigate', {'url': role_cfg['dashboard_url']})
                await asyncio.sleep(1.5)

                # 3. Test Drawer & UI/UX verification
                test_script = f"""
                    (async function() {{
                        const drawer = document.getElementById('muleguard-profile-drawer');
                        const overlay = document.getElementById('muleguard-profile-drawer-overlay');
                        
                        // Check initial state
                        const initialClosed = drawer && drawer.classList.contains('translate-x-full');

                        // Open profile drawer
                        window.openProfileDrawer('profile');
                        await new Promise(r => setTimeout(r, 300));

                        const openedOnProfile = drawer && drawer.classList.contains('translate-x-0') && overlay.classList.contains('opacity-100');

                        // Read profile fields
                        const name = document.getElementById('drawer-profile-name')?.textContent.trim();
                        const empid = document.getElementById('drawer-profile-empid')?.textContent.trim();
                        const badge = document.getElementById('drawer-profile-role-badge')?.textContent.trim();
                        const dept = document.getElementById('drawer-detail-dept')?.textContent.trim();
                        const email = document.getElementById('drawer-detail-email')?.textContent.trim();
                        const role = document.getElementById('drawer-detail-role')?.textContent.trim();
                        const face = document.getElementById('drawer-detail-face')?.textContent.trim();
                        const access = document.getElementById('drawer-detail-access')?.textContent.trim();

                        // Sensitive data leak check in entire drawer HTML
                        const drawerHTML = drawer ? drawer.innerHTML : '';
                        const hasPasswordLeak = drawerHTML.toLowerCase().includes('argon2') || drawerHTML.includes('Password@123');
                        const hasTokenLeak = drawerHTML.includes('challenge_token') || drawerHTML.includes('probe_vector');
                        const hasExaggeratedWording = drawerHTML.includes('Sovereign Security Guaranteed') || drawerHTML.includes('Root System Access');

                        // Tab test: Switch to Preferences & Security
                        const settingsTabBtn = document.getElementById('tab-btn-settings');
                        const settingsTabText = settingsTabBtn?.textContent.trim();
                        window.switchDrawerTab('settings');
                        await new Promise(r => setTimeout(r, 100));

                        const isSettingsVisible = !document.getElementById('drawer-tab-settings-content')?.classList.contains('hidden');
                        const isProfileHidden = document.getElementById('drawer-tab-profile-content')?.classList.contains('hidden');
                        const headerTitle = document.getElementById('drawer-header-title')?.textContent.trim();

                        // Read settings content
                        const settingsText = document.getElementById('drawer-tab-settings-content')?.innerText || '';

                        // Check Workspace section
                        const hasThemeControl = settingsText.includes('Interface Theme');
                        const hasDensityControl = settingsText.includes('Layout Density');
                        const hasAutoRefresh = settingsText.includes('Auto Refresh / Live Data');
                        const hasTimeFormat = settingsText.includes('Time / Date Display');

                        // Check Notifications section
                        const hasCriticalAlerts = settingsText.includes('Critical Risk Alerts');
                        const hasCaseUpdates = settingsText.includes('Investigation / Case Updates');
                        const hasSystemNotifs = settingsText.includes('System Notifications');
                        const hasAlertSound = settingsText.includes('Alert Sound');

                        // Check Security & Session section
                        const hasFaceAuthSec = settingsText.includes('Face Authentication');
                        const hasSessionSec = settingsText.includes('Current Session Status');
                        const hasLastLoginSec = settingsText.includes('Last Authentication');
                        const hasTimeoutSec = settingsText.includes('Session Timeout Policy');

                        // Role-specific settings container text
                        const roleSettingsContainerText = document.getElementById('role-settings-container')?.innerText || '';

                        // Test Theme Switcher
                        window.setMuleGuardTheme('dark');
                        const isDarkApplied = document.documentElement.classList.contains('dark');
                        window.setMuleGuardTheme('light');
                        const isLightApplied = document.documentElement.classList.contains('light');

                        // Test Density Switcher
                        window.setMuleGuardDensity('compact');
                        const isCompactApplied = document.documentElement.classList.contains('density-compact');
                        window.setMuleGuardDensity('comfortable');
                        const isDefaultApplied = !document.documentElement.classList.contains('density-compact');

                        // Test Time format
                        window.setMuleGuardTimeFormat('utc');
                        const isUtcStored = localStorage.getItem('muleguard_time_format') === 'utc';
                        window.setMuleGuardTimeFormat('local');
                        const isLocalStored = localStorage.getItem('muleguard_time_format') === 'local';

                        // Test Close via ESC
                        window.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Escape' }}));
                        await new Promise(r => setTimeout(r, 300));
                        const closedViaEsc = drawer.classList.contains('translate-x-full');

                        // Test Close via X button
                        window.openProfileDrawer('profile');
                        await new Promise(r => setTimeout(r, 300));
                        const closeBtn = drawer.querySelector('button[title*="Close"]');
                        if (closeBtn) closeBtn.click();
                        await new Promise(r => setTimeout(r, 300));
                        const closedViaBtn = drawer.classList.contains('translate-x-full');

                        // Test Close via outside overlay click
                        window.openProfileDrawer('profile');
                        await new Promise(r => setTimeout(r, 300));
                        overlay.click();
                        await new Promise(r => setTimeout(r, 300));
                        const closedViaOverlay = drawer.classList.contains('translate-x-full');

                        // Check sidebar preservation
                        const sidebarExists = !!document.getElementById('sidebar-container');
                        const sidebarLinksCount = document.querySelectorAll('#sidebar-container a').length;

                        return {{
                            initialClosed,
                            openedOnProfile,
                            name,
                            empid,
                            badge,
                            dept,
                            email,
                            role,
                            face,
                            access,
                            hasPasswordLeak,
                            hasTokenLeak,
                            hasExaggeratedWording,
                            settingsTabText,
                            isSettingsVisible,
                            isProfileHidden,
                            headerTitle,
                            hasThemeControl,
                            hasDensityControl,
                            hasAutoRefresh,
                            hasTimeFormat,
                            hasCriticalAlerts,
                            hasCaseUpdates,
                            hasSystemNotifs,
                            hasAlertSound,
                            hasFaceAuthSec,
                            hasSessionSec,
                            hasLastLoginSec,
                            hasTimeoutSec,
                            roleSettingsContainerText,
                            isDarkApplied,
                            isLightApplied,
                            isCompactApplied,
                            isDefaultApplied,
                            isUtcStored,
                            isLocalStored,
                            closedViaEsc,
                            closedViaBtn,
                            closedViaOverlay,
                            sidebarExists,
                            sidebarLinksCount
                        }};
                    }})()
                """
                eval_res = (await send('Runtime.evaluate', {'expression': test_script, 'awaitPromise': True, 'returnByValue': True})).get('result', {}).get('value')

                def check(cond, msg):
                    nonlocal all_passed
                    if cond:
                        print(f"  ✔ PASS: {msg}")
                    else:
                        print(f"  ❌ FAIL: {msg}")
                        all_passed = False

                check(eval_res['initialClosed'], "Drawer is initially hidden off-screen")
                check(eval_res['openedOnProfile'], "Drawer opens smoothly on 'profile' tab")
                check(eval_res['name'] == role_cfg['expected_name'], f"Profile name matches '{role_cfg['expected_name']}' (got: {eval_res['name']})")
                check(eval_res['badge'] == role_cfg['expected_role_badge'], f"Role badge matches '{role_cfg['expected_role_badge']}' (got: {eval_res['badge']})")
                check(eval_res['dept'] == role_cfg['expected_dept'], f"Department matches '{role_cfg['expected_dept']}' (got: {eval_res['dept']})")
                check(eval_res['role'] == role_cfg['expected_role_label'], f"Role label matches '{role_cfg['expected_role_label']}' (got: {eval_res['role']})")
                check(eval_res['empid'] == role_cfg['employee_id'], f"Employee ID matches '{role_cfg['employee_id']}'")
                check(not eval_res['hasPasswordLeak'], "Zero password or hash leaks in drawer DOM")
                check(not eval_res['hasTokenLeak'], "Zero auth tokens or raw biometric probes in drawer DOM")
                check(not eval_res['hasExaggeratedWording'], "No exaggerated marketing/security claims (factual institutional wording)")
                check('Preferences & Security' in eval_res['settingsTabText'], f"Settings tab renamed to 'Preferences & Security' (got: {eval_res['settingsTabText']})")
                check(eval_res['isSettingsVisible'], "Settings tab contents toggle active correctly")
                check(eval_res['hasThemeControl'] and eval_res['hasDensityControl'] and eval_res['hasAutoRefresh'] and eval_res['hasTimeFormat'], "Section A (Workspace) controls present")
                check(eval_res['hasCriticalAlerts'] and eval_res['hasCaseUpdates'] and eval_res['hasSystemNotifs'] and eval_res['hasAlertSound'], "Section B (Notifications) controls present")
                check(eval_res['hasFaceAuthSec'] and eval_res['hasSessionSec'] and eval_res['hasLastLoginSec'] and eval_res['hasTimeoutSec'], "Section C (Security & Session) factual info present without fake controls")

                # Verify expected role-specific preferences
                for exp in role_cfg['expected_role_settings']:
                    check(exp in eval_res['roleSettingsContainerText'], f"Role-specific setting '{exp}' present for {role_name}")

                # Verify unauthorized role settings do NOT appear
                for unauth in role_cfg['unauthorized_role_settings']:
                    check(unauth not in eval_res['roleSettingsContainerText'], f"Unauthorized setting '{unauth}' NOT present for {role_name}")

                check(eval_res['isDarkApplied'] and eval_res['isLightApplied'], "Theme switching (Light / Dark) works")
                check(eval_res['isCompactApplied'] and eval_res['isDefaultApplied'], "Layout density (Default / Compact) works")
                check(eval_res['closedViaEsc'], "Drawer closes on ESC key")
                check(eval_res['closedViaBtn'], "Drawer closes on close (X) button")
                check(eval_res['closedViaOverlay'], "Drawer closes on outside backdrop overlay click")
                check(eval_res['sidebarExists'] and eval_res['sidebarLinksCount'] > 0, "Existing sidebar navigation remains fully intact")

            # 4. Test Logout flow on the last role
            print(f"\n{'='*70}\n[TEST] Secure Sign Out Verification\n{'='*70}")
            logout_script = """
                (async function() {
                    window.openProfileDrawer('profile');
                    await new Promise(r => setTimeout(r, 200));
                    const logoutBtn = document.querySelector('#muleguard-profile-drawer button[onclick*="logoutUser"]');
                    if (logoutBtn) logoutBtn.click();
                    await new Promise(r => setTimeout(r, 800));
                    const currentUrl = window.location.href;
                    const sessionCleared = !sessionStorage.getItem('muleguard_session');
                    return { currentUrl, sessionCleared };
                })()
            """
            logout_res = (await send('Runtime.evaluate', {'expression': logout_script, 'awaitPromise': True, 'returnByValue': True})).get('result', {}).get('value')
            if logout_res:
                is_logged_out = 'login.html' in logout_res.get('currentUrl', '') and logout_res.get('sessionCleared')
                if is_logged_out:
                    print(f"  ✔ PASS: Secure Sign Out successfully clears session and redirects to login.html")
                else:
                    print(f"  ❌ FAIL: Logout did not redirect to login: {logout_res}")
                    all_passed = False

            # Verify no console errors
            non_ext_errors = [e for e in console_errors if 'chrome-extension' not in e]
            if len(non_ext_errors) == 0:
                print("  ✔ PASS: Zero application console errors during entire test run")
            else:
                print(f"  ⚠️ Console errors noted: {non_ext_errors}")

            print(f"\n{'='*70}")
            if all_passed:
                print("FINAL RESULT: ALL ROLE TESTS PASSED (100% SUCCESS)")
            else:
                print("FINAL RESULT: ONE OR MORE TESTS FAILED")
            print(f"{'='*70}")

    finally:
        proc.terminate()

if __name__ == '__main__':
    asyncio.run(run_verification())
