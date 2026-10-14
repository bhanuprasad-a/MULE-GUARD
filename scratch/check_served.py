import urllib.request

with urllib.request.urlopen('http://127.0.0.1:8000/frontend/three.min.js') as res:
    data = res.read().decode('utf-8', errors='ignore')
    print('Length:', len(data))
    print('Has Function("r":', 'Function("r"' in data)
    print('Has globalThis.regeneratorRuntime:', 'globalThis.regeneratorRuntime' in data)

with urllib.request.urlopen('http://127.0.0.1:8000/frontend/three.js') as res:
    data = res.read().decode('utf-8', errors='ignore')
    print('three.js Length:', len(data))
