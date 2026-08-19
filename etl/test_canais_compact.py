"""
test_canais_compact.py — Test compacting canais_by_hierarquia
"""
import os, json
import pandas as pd

DATA_DIR = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\dashboard-acompanhamento-categorias\data"
DAILY_PARQUET = os.path.join(DATA_DIR, 'base_dados_daily.parquet')

df = pd.read_parquet(DAILY_PARQUET)

date_cols_jul_25 = [c for c in df.columns if c.endswith('/07/2025')]
date_cols_jun_26 = [c for c in df.columns if c.endswith('/06/2026')]
date_cols_jul_26 = [c for c in df.columns if c.endswith('/07/2026')]

date_cols_jul_25.sort(key=lambda x: int(x.split('/')[0]))
date_cols_jun_26.sort(key=lambda x: int(x.split('/')[0]))
date_cols_jul_26.sort(key=lambda x: int(x.split('/')[0]))

agg_dates = {c: 'sum' for c in date_cols_jul_25 + date_cols_jun_26 + date_cols_jul_26}
grp = df.groupby(['grupo', 'linha', 'canal'], as_index=False).agg(agg_dates)

digital_kw = ['APP', 'E-COMMERCE', 'E_COMMERCE', 'IFOOD', 'SITE', 'MERCADO LIVRE', 'PLATAFORMAS', 'WHATSAPP']
tele_kw = ['TELE ENCAMINHADA LOJAS', 'TELE VIZINHAN', 'VENDA TELE ENTREGA', 'VENDA TELE ENTREGA CENTRAL', 'TELEVENDAS', 'DELIVERY']

def get_channel_group(canal_name):
    c_up = canal_name.upper()
    if any(k in c_up for k in digital_kw): return 'digital'
    if any(k in c_up for k in tele_kw): return 'tele'
    return 'loja'

grp['canal_grupo'] = grp['canal'].apply(get_channel_group)

records = []
for _, r in grp.iterrows():
    d25 = [round(float(r[c]), 1) for c in date_cols_jul_25]
    d26_06 = [round(float(r[c]), 1) for c in date_cols_jun_26]
    d26_07 = [round(float(r[c]), 1) for c in date_cols_jul_26]
    records.append({
        'g': r['grupo'], 'l': r['linha'], 'c': r['canal'], 'cg': r['canal_grupo'],
        'v26': round(sum(d26_07), 1), 'v26_06': round(sum(d26_06), 1), 'v25': round(sum(d25), 1),
        'd25': d25, 'd26_06': d26_06, 'd26_07': d26_07
    })

s = json.dumps(records, ensure_ascii=False, separators=(',', ':'))
print(f"Total records: {len(records)}")
print(f"Size of canais_by_hierarquia JSON: {len(s) / (1024*1024):.2f} MB")
