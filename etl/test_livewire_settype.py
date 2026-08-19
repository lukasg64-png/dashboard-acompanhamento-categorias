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

# 2. Get New Resource page & extract component snapshot
resp = opener.open('http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/new')
html = resp.read().decode('utf-8')

token_match = re.search(r'csrf-token"\s+content="([^"]+)"', html) or re.search(r'name="_token"\s+value="([^"]+)"', html)
page_csrf = token_match.group(1) if token_match else csrf_token

component = None
for m in re.finditer(r'wire:snapshot="([^"]+)"', html):
    raw = m.group(1).replace('&quot;', '"')
    data = json.loads(raw)
    if data.get('memo', {}).get('name') == 'project.resource.create':
        component = data
        break

print("Encontrado componente:", component['memo']['name'], "ID:", component['memo']['id'])

# 3. Call Livewire update with setType
livewire_payload = {
    "_token": page_csrf,
    "components": [
        {
            "snapshot": json.dumps(component),
            "updates": {},
            "calls": [
                {
                    "path": "",
                    "method": "setType",
                    "params": ["private-deploy-key"]
                }
            ]
        }
    ]
}

req_lw = urllib.request.Request(
    'http://10.200.12.69:8000/livewire/update',
    data=json.dumps(livewire_payload).encode('utf-8'),
    method='POST'
)
req_lw.add_header('Content-Type', 'application/json')
req_lw.add_header('X-CSRF-TOKEN', page_csrf)
req_lw.add_header('X-Livewire', 'true')

try:
    resp = opener.open(req_lw)
    res_data = json.loads(resp.read().decode('utf-8'))
    print("Resposta Livewire setType('private-deploy-key'):")
    print(json.dumps(res_data, indent=2)[:1000])
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code, e.read().decode('utf-8'))

