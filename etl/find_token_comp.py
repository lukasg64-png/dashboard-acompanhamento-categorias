import urllib.request, urllib.parse, http.cookiejar, re, json, sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Login
resp = opener.open('http://10.200.12.69:8000/login')
html = resp.read().decode('utf-8')
csrf_token = re.search(r'name="_token"\s+value="([^"]+)"', html).group(1)

login_data = urllib.parse.urlencode({
    '_token': csrf_token,
    'email': 'fsjplan.dados@gmail.com',
    'password': 'ecommerce2026'
}).encode('utf-8')
req = urllib.request.Request('http://10.200.12.69:8000/login', data=login_data, method='POST')
opener.open(req)

# 2. Get API Tokens page
resp = opener.open('http://10.200.12.69:8000/security/api-tokens')
html = resp.read().decode('utf-8')

# Find the component with 'api-token' or 'tokens'
matches = re.findall(r'wire:snapshot="([^"]+)"', html)
for m in matches:
    raw = m.replace('&quot;', '"')
    if 'token' in raw.lower():
        data = json.loads(raw)
        print("Component:", data.get('memo', {}).get('name'))
        print("Snapshot:", json.dumps(data, indent=2)[:500])

