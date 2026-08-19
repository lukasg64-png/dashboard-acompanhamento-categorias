import json
with open('data/agosto/canais_summary.json', 'r', encoding='utf-8') as f:
    canais = json.load(f)

for d in range(1, 20):
    v26_d = sum(c['d26_07'][d-1] for c in canais)
    v26_06_d = sum(c['d26_06'][d-1] for c in canais)
    v25_d = sum(c['d25'][d-1] for c in canais)
    print(f"Dia {d:02d}: Ago/26 = R$ {v26_d:,.2f} | Jul/26 = R$ {v26_06_d:,.2f} | Ago/25 = R$ {v25_d:,.2f}")

tot26_19 = sum(sum(c['d26_07'][:19]) for c in canais)
tot26_06_19 = sum(sum(c['d26_06'][:19]) for c in canais)
tot25_19 = sum(sum(c['d25'][:19]) for c in canais)

print("\n" + "="*60)
print(f"TOTAL 01 a 19 Ago/26: R$ {tot26_19:,.2f}")
print(f"TOTAL 01 a 19 Jul/26: R$ {tot26_06_19:,.2f} | MoM: {((tot26_19/tot26_06_19)-1)*100:+.2f}%")
print(f"TOTAL 01 a 19 Ago/25: R$ {tot25_19:,.2f} | YoY: {((tot26_19/tot25_19)-1)*100:+.2f}%")
print("="*60)
