import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedir(), urllib.request.HTTPSHandler(context=ctx))

req1 = urllib.request.Request('https://sense.farmaciassaojoao.com.br/hub/', headers={'User-Agent': 'Mozilla/5.0'})
try:
    res1 = opener.open(req1)
    target_url = res1.headers.get('Location')
except Exception as e:
    target_url = e.headers.get('Location')

print('Step 1 target_url:', target_url)

req2 = urllib.request.Request(target_url, headers={'User-Agent': 'Mozilla/5.0'})
res2 = opener.open(req2)
html = res2.read().decode('utf-8', errors='ignore')

print('HTML length:', len(html))
print('Form tag:', re.findall(r'<form[^>]*>', html))
print('Scripts:', re.findall(r'<script[^>]*src=["\']([^"\']*)["\']', html))
print('Form HTML snippet:', html[html.find('<form'):html.find('</form>')+10])
