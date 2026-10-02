import subprocess, time, json, urllib.request, os

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
user_data_dir = os.path.join(os.environ['TEMP'], 'chrome_test_profile')

# Start Chrome in headless mode with remote debugging
cmd = [
    chrome_path,
    '--headless=new',
    '--remote-debugging-port=9222',
    f'--user-data-dir={user_data_dir}',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    'about:blank'
]

proc = subprocess.Popen(cmd)
time.sleep(2)

try:
    # Get WebSocket URL for the browser tab
    version_url = 'http://127.0.0.1:9222/json'
    tabs = json.loads(urllib.request.urlopen(version_url).read())
    tab = tabs[0]
    ws_url = tab['webSocketDebuggerUrl']
    print('Chrome connected:', ws_url)
    
except Exception as e:
    print('Failed to connect to Chrome:', e)
finally:
    proc.terminate()
