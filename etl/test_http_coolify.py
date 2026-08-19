import urllib.request, urllib.parse, http.cookiejar, re, json, sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. GET login page
print("1. Obtendo página de login e token CSRF...")
resp = opener.open('http://10.200.12.69:8000/login')
html = resp.read().decode('utf-8')

token_match = re.search(r'name="_token"\s+value="([^"]+)"', html) or re.search(r'value="([^"]+)"\s+name="_token"', html)
csrf_token = token_match.group(1) if token_match else ''
print("CSRF Token:", csrf_token)

# 2. POST login
print("2. Enviando credenciais...")
login_data = urllib.parse.urlencode({
    '_token': csrf_token,
    'email': 'fsjplan.dados@gmail.com',
    'password': 'ecommerce2026'
}).encode('utf-8')

req = urllib.request.Request('http://10.200.12.69:8000/login', data=login_data, method='POST')
req.add_header('Content-Type', 'application/x-www-form-urlencoded')

try:
    resp = opener.open(req)
    print("Login status:", resp.status, "URL:", resp.url)
except urllib.error.HTTPError as e:
    print("Login redirect/status:", e.code, "URL:", e.url)

# 3. GET API tokens page
resp = opener.open('http://10.200.12.69:8000/security/api-tokens')
html = resp.read().decode('utf-8')
print("Página de tokens obtida com sucesso! Tamanho:", len(html))

# Procurar tokens ou Livewire snapshot
for m in re.finditer(r'wire:snapshot="([^"]+)"', html):
    raw = m.group(1).replace('&quot;', '"')
    print("Livewire snapshot:", raw[:300])

