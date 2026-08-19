"""Check if loadAllData was replaced or if fetch is still inside dist/index.html"""
import os

DIST_FILE = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\dashboard-acompanhamento-categorias\dist\index.html"

with open(DIST_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

print("Contains fetch('data/:", "fetch('data/" in content)
print("Contains _PACKED:", "_PACKED" in content)
print("Contains _decompress:", "_decompress" in content)

# Find loadAllData definition in content
idx = content.find("function loadAllData()")
if idx != -1:
    print("\nloadAllData snippet:")
    print(content[idx:idx+400])
