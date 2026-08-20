import json

with open('data/agosto/hierarquia_detalhada.json', 'r', encoding='utf-8') as f:
    hier = json.load(f)
with open('data/agosto/filtro_hierarquia.json', 'r', encoding='utf-8') as f:
    fh = json.load(f)

print('FH Diretores:', fh.get('diretores'))
h_dirs = set(h.get('diretor') for h in hier)
print('Hier unique diretores:', h_dirs)

for d in fh.get('diretores', []):
    matching = [h for h in hier if h.get('diretor') == d]
    print(f'Director "{d}" matching hier rows: {len(matching)}')
    distritais_for_d = set(h.get('distrital') for h in matching)
    print(f'Distritais for "{d}": {distritais_for_d}')
