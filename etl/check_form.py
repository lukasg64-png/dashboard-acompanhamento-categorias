import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://sense.farmaciassaojoao.com.br/internal_forms_authentication/', headers={'User-Agent': 'Mozilla/5.0'})
res = urllib.request.urlopen(req, context=ctx)
html = res.read().decode('utf-8', errors='ignore')

print('Form action:', re.findall(r'<form[^>]*action=["\']([^"\']*)["\']', html, re.I))
print('Inputs:', re.findall(r'<input[^>]*>', html, re.I))
