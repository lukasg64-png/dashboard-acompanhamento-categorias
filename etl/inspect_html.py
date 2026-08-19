"""
inspect_html.py — Check dist/index.html for syntax errors or missing elements.
"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_FILE = os.path.join(BASE, 'dist', 'index.html')

with open(DIST_FILE, 'r', encoding='utf-8') as f:
    html = f.read()

print("File size:", len(html), "bytes")
print("Has _PACKED:", '_PACKED' in html)
print("Has loadAllData:", 'loadAllData' in html)

# Print first 500 chars and script tags
import re
scripts = re.findall(r'<script.*?>.*?</script>', html, re.DOTALL)
print(f"Total script tags: {len(scripts)}")
for i, s in enumerate(scripts):
    print(f"\n--- Script {i} ({len(s)} chars) ---")
    print(s[:300] + "...")
