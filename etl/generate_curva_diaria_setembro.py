"""
generate_curva_diaria_setembro.py — Gera curva_diaria.json com os pesos exatos informados pelo usuário
"""
import json, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'setembro')
os.makedirs(DATA_DIR, exist_ok=True)

# Tabela fornecida pelo usuário
TABELA_PESOS = [
    {"dia": 1,  "dia_semana": "Terça",   "peso": 1.034},
    {"dia": 2,  "dia_semana": "Quarta",  "peso": 1.082},
    {"dia": 3,  "dia_semana": "Quinta",  "peso": 1.033},
    {"dia": 4,  "dia_semana": "Sexta",   "peso": 1.112},
    {"dia": 5,  "dia_semana": "Sábado",  "peso": 1.005},
    {"dia": 6,  "dia_semana": "Domingo", "peso": 0.695},
    {"dia": 7,  "dia_semana": "Segunda", "peso": 1.039},
    {"dia": 8,  "dia_semana": "Terça",   "peso": 1.034},
    {"dia": 9,  "dia_semana": "Quarta",  "peso": 1.082},
    {"dia": 10, "dia_semana": "Quinta",  "peso": 1.033},
    {"dia": 11, "dia_semana": "Sexta",   "peso": 1.112},
    {"dia": 12, "dia_semana": "Sábado",  "peso": 1.005},
    {"dia": 13, "dia_semana": "Domingo", "peso": 0.695},
    {"dia": 14, "dia_semana": "Segunda", "peso": 1.039},
    {"dia": 15, "dia_semana": "Terça",   "peso": 1.034},
    {"dia": 16, "dia_semana": "Quarta",  "peso": 1.082},
    {"dia": 17, "dia_semana": "Quinta",  "peso": 1.033},
    {"dia": 18, "dia_semana": "Sexta",   "peso": 1.112},
    {"dia": 19, "dia_semana": "Sábado",  "peso": 1.005},
    {"dia": 20, "dia_semana": "Domingo", "peso": 0.695},
    {"dia": 21, "dia_semana": "Segunda", "peso": 1.039},
    {"dia": 22, "dia_semana": "Terça",   "peso": 1.034},
    {"dia": 23, "dia_semana": "Quarta",  "peso": 1.082},
    {"dia": 24, "dia_semana": "Quinta",  "peso": 1.033},
    {"dia": 25, "dia_semana": "Sexta",   "peso": 1.112},
    {"dia": 26, "dia_semana": "Sábado",  "peso": 1.005},
    {"dia": 27, "dia_semana": "Domingo", "peso": 0.695},
    {"dia": 28, "dia_semana": "Segunda", "peso": 1.039},
    {"dia": 29, "dia_semana": "Terça",   "peso": 1.034},
    {"dia": 30, "dia_semana": "Quarta",  "peso": 1.082}
]

META_MENSAL_TOTAL = 898116411.32

soma_pesos = sum(item["peso"] for item in TABELA_PESOS)
print(f"Soma dos pesos dos 30 dias: {soma_pesos:.4f}")

curva = []
acum_pct = 0.0
acum_meta = 0.0

for item in TABELA_PESOS:
    pct_dia = item["peso"] / soma_pesos
    acum_pct += pct_dia
    meta_dia = round(META_MENSAL_TOTAL * pct_dia, 2)
    acum_meta = round(META_MENSAL_TOTAL * acum_pct, 2)
    
    curva.append({
        "dia": item["dia"],
        "dia_semana": item["dia_semana"],
        "peso": item["peso"],
        "pct_dia": round(pct_dia, 10),
        "pct_acum": round(acum_pct, 10),
        "proj_dia": meta_dia,
        "proj_acum": acum_meta,
        "meta_dia": meta_dia,
        "meta_acum": acum_meta
    })

# Garantir 100% exato no último dia
curva[-1]["pct_acum"] = 1.0
curva[-1]["meta_acum"] = META_MENSAL_TOTAL
curva[-1]["proj_acum"] = META_MENSAL_TOTAL

output_file = os.path.join(DATA_DIR, 'curva_diaria.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(curva, f, indent=2, ensure_ascii=False)

print(f"[OK] Curva gerada com sucesso em {output_file}")
for c in curva[:5]:
    print(f"  Dia {c['dia']:>2} ({c['dia_semana']:<7}): Peso {c['peso']:.3f} | {c['pct_dia']*100:.2f}% dia | {c['pct_acum']*100:.2f}% acum | Meta Acum: R$ {c['meta_acum']:,.2f}")
