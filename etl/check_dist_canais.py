"""Check renderCanais inside dist/index.html"""
import os

DIST_FILE = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\dashboard-acompanhamento-categorias\dist\index.html"

with open(DIST_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

print("Contains toggleChGroup:", "toggleChGroup" in content)
print("Contains Venda Digital:", "Venda Digital" in content)
print("Contains EMPRESA TOTAL:", "EMPRESA TOTAL" in content)

# Print renderCanais function from dist/index.html
idx = content.find("function renderCanais()")
if idx != -1:
    print("\nrenderCanais snippet from dist/index.html:")
    print(content[idx:idx+600])
