"""
generate_curva_diaria_setembro.py — Tabela completa de pesos e curva diária enviada pelo usuário
"""
import json, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'setembro')
os.makedirs(DATA_DIR, exist_ok=True)

# Tabela completa enviada pelo usuário (com Meta +16% Acum. R$)
TABELA_OFICIAL_USER = [
    {"dia": 1,  "dia_semana": "Terça",   "peso": 1.034, "pct_mes_str": "3,4%", "meta_acum_user": 30829388},
    {"dia": 2,  "dia_semana": "Quarta",  "peso": 1.082, "pct_mes_str": "3,6%", "meta_acum_user": 63115194},
    {"dia": 3,  "dia_semana": "Quinta",  "peso": 1.033, "pct_mes_str": "3,4%", "meta_acum_user": 93914171},
    {"dia": 4,  "dia_semana": "Sexta",   "peso": 1.112, "pct_mes_str": "3,7%", "meta_acum_user": 127083285},
    {"dia": 5,  "dia_semana": "Sábado",  "peso": 1.005, "pct_mes_str": "3,3%", "meta_acum_user": 157049605},
    {"dia": 6,  "dia_semana": "Domingo", "peso": 0.695, "pct_mes_str": "2,3%", "meta_acum_user": 177790915},
    {"dia": 7,  "dia_semana": "Segunda", "peso": 1.039, "pct_mes_str": "3,5%", "meta_acum_user": 208791627},
    {"dia": 8,  "dia_semana": "Terça",   "peso": 1.034, "pct_mes_str": "3,4%", "meta_acum_user": 239621015},
    {"dia": 9,  "dia_semana": "Quarta",  "peso": 1.082, "pct_mes_str": "3,6%", "meta_acum_user": 271906821},
    {"dia": 10, "dia_semana": "Quinta",  "peso": 1.033, "pct_mes_str": "3,4%", "meta_acum_user": 302705798},
    {"dia": 11, "dia_semana": "Sexta",   "peso": 1.112, "pct_mes_str": "3,7%", "meta_acum_user": 335874912},
    {"dia": 12, "dia_semana": "Sábado",  "peso": 1.005, "pct_mes_str": "3,3%", "meta_acum_user": 365841232},
    {"dia": 13, "dia_semana": "Domingo", "peso": 0.695, "pct_mes_str": "2,3%", "meta_acum_user": 386582542},
    {"dia": 14, "dia_semana": "Segunda", "peso": 1.039, "pct_mes_str": "3,5%", "meta_acum_user": 417583254},
    {"dia": 15, "dia_semana": "Terça",   "peso": 1.034, "pct_mes_str": "3,4%", "meta_acum_user": 448412642},
    {"dia": 16, "dia_semana": "Quarta",  "peso": 1.082, "pct_mes_str": "3,6%", "meta_acum_user": 480698449},
    {"dia": 17, "dia_semana": "Quinta",  "peso": 1.033, "pct_mes_str": "3,4%", "meta_acum_user": 511497425},
    {"dia": 18, "dia_semana": "Sexta",   "peso": 1.112, "pct_mes_str": "3,7%", "meta_acum_user": 544666539},
    {"dia": 19, "dia_semana": "Sábado",  "peso": 1.005, "pct_mes_str": "3,3%", "meta_acum_user": 574632859},
    {"dia": 20, "dia_semana": "Domingo", "peso": 0.695, "pct_mes_str": "2,3%", "meta_acum_user": 595374169},
    {"dia": 21, "dia_semana": "Segunda", "peso": 1.039, "pct_mes_str": "3,5%", "meta_acum_user": 626374881},
    {"dia": 22, "dia_semana": "Terça",   "peso": 1.034, "pct_mes_str": "3,4%", "meta_acum_user": 657204269},
    {"dia": 23, "dia_semana": "Quarta",  "peso": 1.082, "pct_mes_str": "3,6%", "meta_acum_user": 689490076},
    {"dia": 24, "dia_semana": "Quinta",  "peso": 1.033, "pct_mes_str": "3,4%", "meta_acum_user": 720289052},
    {"dia": 25, "dia_semana": "Sexta",   "peso": 1.112, "pct_mes_str": "3,7%", "meta_acum_user": 753458166},
    {"dia": 26, "dia_semana": "Sábado",  "peso": 1.005, "pct_mes_str": "3,3%", "meta_acum_user": 783424486},
    {"dia": 27, "dia_semana": "Domingo", "peso": 0.695, "pct_mes_str": "2,3%", "meta_acum_user": 804165796},
    {"dia": 28, "dia_semana": "Segunda", "peso": 1.039, "pct_mes_str": "3,5%", "meta_acum_user": 835166508},
    {"dia": 29, "dia_semana": "Terça",   "peso": 1.034, "pct_mes_str": "3,4%", "meta_acum_user": 865995896},
    {"dia": 30, "dia_semana": "Quarta",  "peso": 1.082, "pct_mes_str": "3,6%", "meta_acum_user": 898281703}
]

TOTAL_USER = TABELA_OFICIAL_USER[-1]["meta_acum_user"]
META_MENSAL_OFICIAL = 898116411.32

curva = []
prev_acum = 0.0

for i, item in enumerate(TABELA_OFICIAL_USER):
    pct_acum = item["meta_acum_user"] / TOTAL_USER
    pct_dia = pct_acum - prev_acum
    prev_acum = pct_acum
    
    meta_acum = round(META_MENSAL_OFICIAL * pct_acum, 2)
    meta_dia = round(META_MENSAL_OFICIAL * pct_dia, 2)
    
    curva.append({
        "dia": item["dia"],
        "dia_semana": item["dia_semana"],
        "peso": item["peso"],
        "pct_mes_str": item["pct_mes_str"],
        "pct_dia": round(pct_dia, 10),
        "pct_acum": round(pct_acum, 10),
        "meta_acum_tabela_user": item["meta_acum_user"],
        "proj_dia": meta_dia,
        "proj_acum": meta_acum,
        "meta_dia": meta_dia,
        "meta_acum": meta_acum
    })

curva[-1]["pct_acum"] = 1.0
curva[-1]["meta_acum"] = META_MENSAL_OFICIAL
curva[-1]["proj_acum"] = META_MENSAL_OFICIAL

output_file = os.path.join(DATA_DIR, 'curva_diaria.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(curva, f, indent=2, ensure_ascii=False)

print(f"[OK] Curva gerada com sucesso em {output_file}")
for c in curva[:6]:
    print(f"  Dia {c['dia']:>2} ({c['dia_semana']:<7}): Peso {c['peso']:.3f} | {c['pct_dia']*100:.2f}% | Meta Acum Tabela: R$ {c['meta_acum_tabela_user']:>11,d} | Meta Dashboard: R$ {c['meta_acum']:>14,.2f}")
