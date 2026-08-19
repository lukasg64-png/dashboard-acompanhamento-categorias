import json, sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

with open('data/agosto/canais_summary.json', encoding='utf-8') as f:
    canais = json.load(f)
with open('data/agosto/categorias_summary.json', encoding='utf-8') as f:
    cats = json.load(f)
with open('data/agosto/executive_kpis.json', encoding='utf-8') as f:
    kpis = json.load(f)

total_canais = sum(c['venda_jul_26'] for c in canais)
total_cats   = sum(c['venda_jul_26'] for c in cats)
mom_canais   = sum(c['venda_jun_26'] for c in canais)
mom_cats     = sum(c['venda_jun_26'] for c in cats)
yoy_canais   = sum(c['venda_jul_25'] for c in canais)
yoy_cats     = sum(c['venda_jul_25'] for c in cats)

print('=== VERIFICAÇÃO DE CONSISTÊNCIA ===')
print(f'Canais  Ago/26 : R$ {total_canais:>18,.2f}')
print(f'Cats    Ago/26 : R$ {total_cats:>18,.2f}  | Diff: R$ {total_cats-total_canais:+,.2f}')
print(f'Canais  Jul/26 : R$ {mom_canais:>18,.2f}')
print(f'Cats    Jul/26 : R$ {mom_cats:>18,.2f}  | Diff: R$ {mom_cats-mom_canais:+,.2f}')
print(f'Canais  Ago/25 : R$ {yoy_canais:>18,.2f}')
print(f'Cats    Ago/25 : R$ {yoy_cats:>18,.2f}  | Diff: R$ {yoy_cats-yoy_canais:+,.2f}')
print()
kpi = kpis['total_empresa']
print(f"KPI Total : R$ {kpi['venda_jul_26']:>18,.2f}")
print(f"KPI MoM   : {kpi['mom_pct']:+.2f}%")
print(f"KPI YoY   : {kpi['yoy_pct']:+.2f}%")
print(f"Periodo   : {kpis['periodo_info']['periodo_str']}")
