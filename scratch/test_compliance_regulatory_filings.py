import asyncio
import subprocess
import json
import os
import sys
import urllib.request
import websockets

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_filings_page():
    print("====================================================")
    print("TESTING COMPLIANCE REGULATORY FILINGS IN REAL BROWSER")
    print("====================================================")

    cmd = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        '--remote-debugging-port=9456',
        '--remote-allow-origins=*',
        'about:blank'
    ]
    proc = subprocess.Popen(cmd)
    await asyncio.sleep(1.5)

    try:
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9456/json').read())
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
                'width': 1440,
                'height': 900,
                'deviceScaleFactor': 1,
                'mobile': False
            })

            # Navigate to login
            await send('Page.navigate', {'url': 'http://127.0.0.1:8000/frontend/login.html'})
            await asyncio.sleep(0.6)

            # Login as Compliance Officer (MG-CMP-001)
            login_js = """
                (async function() {
                    const res1 = await fetch('/api/v1/auth/stage1-login', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ employee_id: 'MG-CMP-001', password: 'Password@123' })
                    });
                    const d1 = await res1.json();
                    const resV = await fetch('/api/v1/auth/demo-probe-vector', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ employee_id: 'MG-CMP-001', noise_level: 0.0 })
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
                    return d2.user.role;
                })()
            """
            role_eval = await send('Runtime.evaluate', {'expression': login_js, 'awaitPromise': True})
            role = role_eval.get('result', {}).get('value')
            print(f"Logged in as role: {role}")
            assert role == "bank_compliance", f"Expected bank_compliance, got {role}"

            # Navigate to Regulatory Filings
            console_errors.clear()
            filings_url = 'http://127.0.0.1:8000/frontend/bank/compliance/regulatory-filings.html'
            await send('Page.navigate', {'url': filings_url})
            await asyncio.sleep(2.0)

            # Check DOM Elements
            verify_js = """
                (function() {
                    const title = document.querySelector('h1')?.textContent || '';
                    const totalKpi = document.getElementById('kpi-total-filings')?.textContent || '';
                    const draftKpi = document.getElementById('kpi-draft-filings')?.textContent || '';
                    const submittedKpi = document.getElementById('kpi-submitted-filings')?.textContent || '';
                    const acceptedKpi = document.getElementById('kpi-accepted-filings')?.textContent || '';
                    const rows = document.querySelectorAll('#filings-table-body tr');
                    const activeNav = document.getElementById('nav-link-regulatory-filings')?.className || '';
                    
                    return {
                        title,
                        totalKpi,
                        draftKpi,
                        submittedKpi,
                        acceptedKpi,
                        rowCount: rows.length,
                        activeNavContainsActive: activeNav.includes('border-secondary-container') || activeNav.includes('bg-secondary-container')
                    };
                })()
            """
            eval_res = await send('Runtime.evaluate', {'expression': verify_js, 'returnByValue': True})
            data = eval_res.get('result', {}).get('value', {})
            print("DOM Inspection Results:", json.dumps(data, indent=2))

            assert "Regulatory Filings" in data["title"]
            print("✔ PASS: Page title rendered correctly")

            assert int(data["totalKpi"]) >= 4
            assert int(data["draftKpi"]) >= 1
            assert int(data["submittedKpi"]) >= 1
            assert int(data["acceptedKpi"]) >= 1
            print("✔ PASS: All 4 summary KPI cards display live database counts")

            assert data["rowCount"] >= 4
            print(f"✔ PASS: Filings table rendered {data['rowCount']} live database rows")

            assert data["activeNavContainsActive"]
            print("✔ PASS: Sidebar active link correctly highlights 'Regulatory Filings'")

            # Verify no console errors
            print(f"Console Errors Count: {len(console_errors)}")
            assert len(console_errors) == 0, f"Console errors present: {console_errors}"
            print("✔ PASS: Zero browser console errors")

            # Test creating a new filing through UI JavaScript invocation
            create_js = """
                (async function() {
                    const res = await window.MuleGuardAPI.createFiling({
                        account_id: 'ACC-982054',
                        filing_type: 'SAR',
                        reason: 'Browser Automated Submission Test',
                        narrative: 'Testing UI to PostgreSQL live data persistence.',
                        reporting_authority: 'FIU-IND'
                    });
                    await loadFilings();
                    return res.id;
                })()
            """
            created_eval = await send('Runtime.evaluate', {'expression': create_js, 'awaitPromise': True})
            new_id = created_eval.get('result', {}).get('value')
            assert new_id and new_id.startswith('FIL-'), f"Creation failed: {new_id}"
            print(f"✔ PASS: Successfully created new filing {new_id} via API in browser")

            # Re-check KPI counts after creation
            eval_res2 = await send('Runtime.evaluate', {'expression': verify_js, 'returnByValue': True})
            data2 = eval_res2.get('result', {}).get('value', {})
            assert int(data2["totalKpi"]) == int(data["totalKpi"]) + 1
            assert int(data2["draftKpi"]) == int(data["draftKpi"]) + 1
            print(f"✔ PASS: Total KPI incremented to {data2['totalKpi']}, Draft KPI incremented to {data2['draftKpi']}")

            # Clean up test filing
            cleanup_js = f"""
                (async function() {{
                    // Clean up test filing directly from DB
                    return '{new_id}';
                }})()
            """
            await send('Runtime.evaluate', {'expression': cleanup_js, 'awaitPromise': True})
            
            # Clean up from PostgreSQL backend
            from app.db.database import get_connection
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM audit_logs WHERE entity_id = %s;", (new_id,))
                    cur.execute("DELETE FROM regulatory_filings WHERE id = %s;", (new_id,))
                    conn.commit()
            print("✔ PASS: Cleaned up temporary test filing")

            # Final check on console errors
            assert len(console_errors) == 0, f"Console errors present: {console_errors}"
            print("✔ PASS: Zero console errors during complete test session")

            print("\n====================================================")
            print("ALL BROWSER AUTOMATION TESTS COMPLETED SUCCESSFULLY!")
            print("====================================================")

    finally:
        proc.terminate()

if __name__ == '__main__':
    asyncio.run(test_filings_page())
