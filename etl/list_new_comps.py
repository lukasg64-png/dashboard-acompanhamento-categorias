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

# 2. Get New Resource page
resp = opener.open('http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/new')
html = resp.read().decode('utf-8')

for m in re.finditer(r'wire:snapshot="([^"]+)"', html):
    raw = m.group(1).replace('&quot;', '"')
    data = json.loads(raw)
    name = data.get('memo', {}).get('name')
    d = data.get('data')
    keys = list(d.keys()) if isinstance(d, dict) else [type(d).__name__]
    print("Component:", name, "ID:", data.get('memo', {}).get('id'), "Data keys:", keys)

