import urllib.request, urllib.parse, http.cookiejar, ssl

qlik_url = 'https://sense.farmaciassaojoao.com.br'
username = 'lucas.alves6'
password = 'Eloise2025*'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(NoRedir(), urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(context=ctx))

# Step 1: GET /hub/
req1 = urllib.request.Request(f'{qlik_url}/hub/', headers={'User-Agent': 'Mozilla/5.0'})
try:
    res1 = opener.open(req1)
    target_url = res1.headers.get('Location')
except Exception as e:
    target_url = e.headers.get('Location')

print('Target URL:', target_url)

# Step 2: GET target_url
req2 = urllib.request.Request(target_url, headers={'User-Agent': 'Mozilla/5.0'})
res2 = opener.open(req2)
print('Step 2 cookies:', [f"{c.name}={c.value}" for c in cj])

# Step 3: POST credentials
post_data = urllib.parse.urlencode({'username': username, 'pwd': password}).encode('utf-8')
req3 = urllib.request.Request(target_url, data=post_data, headers={
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': target_url
})

try:
    res3 = opener.open(req3)
    print('Step 3 Status:', res3.getcode())
    print('Step 3 Location:', res3.headers.get('Location'))
    print('Step 3 Cookies:', [f"{c.name}={c.value}" for c in cj])
    body = res3.read().decode('utf-8', errors='ignore')
    print('Step 3 Body snippet:', body[:500])
except Exception as e:
    print('Step 3 Error:', e)
