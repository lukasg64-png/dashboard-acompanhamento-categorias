"""
check_ids.py — Check all sel('...') IDs in app.js against index.html.
"""
import os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_FILE = os.path.join(BASE, 'index.html')
JS_APP = os.path.join(BASE, 'js', 'app.js')

with open(HTML_FILE, 'r', encoding='utf-8') as f:
    html = f.read()

with open(JS_APP, 'r', encoding='utf-8') as f:
    js = f.read()

# Extract sel('xxx')
js_ids = set(re.findall(r"sel\(['\"](.*?)['\"]\)", js))

# Extract id="xxx" from html
html_ids = set(re.findall(r'id=["\'](.*?)["\']', html))

missing = js_ids - html_ids
print("Total IDs in JS:", len(js_ids))
print("Total IDs in HTML:", len(html_ids))
print("Missing IDs referenced in JS but not in HTML:", missing)
