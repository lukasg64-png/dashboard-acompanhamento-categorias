import json

with open('data/setembro/hierarquia_detalhada.json', 'r', encoding='utf-8') as f:
    hier = json.load(f)

print(f"Total rows in hierarquia_detalhada: {len(hier)}")

# Sum total venda_jul_26 (Setembro 2026 sales)
tot_set26 = sum(r.get('venda_jul_26', 0) for r in hier)
tot_ago26 = sum(r.get('venda_jun_26', 0) for r in hier)
tot_set25 = sum(r.get('venda_jul_25', 0) for r in hier)

print(f"Total Setembro/26 (D-1): R$ {tot_set26:,.2f}")
print(f"Total Agosto/26: R$ {tot_ago26:,.2f}")
print(f"Total Setembro/25: R$ {tot_set25:,.2f}")

# Group by Diretor
by_diretor = {}
by_distrital = {}
by_distrital_linha = {}

for r in hier:
    d = r.get('diretor') or 'Sem Diretor'
    dist = r.get('distrital') or 'Sem Distrital'
    linha = r.get('linha') or 'Sem Linha'
    grupo = r.get('grupo') or 'Sem Grupo'
    val = r.get('venda_jul_26', 0)

    by_diretor[d] = by_diretor.get(d, 0) + val
    
    if dist not in by_distrital:
        by_distrital[dist] = {'diretor': d, 'venda_set26': 0, 'linhas': set()}
    by_distrital[dist]['venda_set26'] += val
    by_distrital[dist]['linhas'].add(linha)

    key = (dist, linha)
    by_distrital_linha[key] = by_distrital_linha.get(key, 0) + val

print("\n--- Realizado Setembro 2026 por Diretor ---")
for d, v in sorted(by_diretor.items()):
    print(f"  Diretor: {d} -> R$ {v:,.2f} ({v/tot_set26*100:.1f}%)")

print("\n--- Realizado Setembro 2026 por Distrital ---")
for dist, info in sorted(by_distrital.items()):
    v = info['venda_set26']
    d = info['diretor']
    n_lin = len(info['linhas'])
    print(f"  Distrital: {dist:20s} (Diretor: {d:18s}) -> R$ {v:12,.2f} ({v/tot_set26*100:4.1f}%) | {n_lin} linhas")
