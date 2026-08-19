"""
test_canais_compilation.py — Test channel compilation logic and verify sales.
"""
import os, json
import pandas as pd
import numpy as np

DATA_DIR = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\dashboard-acompanhamento-categorias\data"
DAILY_PARQUET = os.path.join(DATA_DIR, 'base_dados_daily.parquet')

df = pd.read_parquet(DAILY_PARQUET)

date_cols_jul_25 = [c for c in df.columns if c.endswith('/07/2025')]
date_cols_jun_26 = [c for c in df.columns if c.endswith('/06/2026')]
date_cols_jul_26 = [c for c in df.columns if c.endswith('/07/2026')]

df['venda_jul_25'] = df[date_cols_jul_25].sum(axis=1)
df['venda_jun_26'] = df[date_cols_jun_26].sum(axis=1)
df['venda_jul_26'] = df[date_cols_jul_26].sum(axis=1)

# Unique channels in data
channels = df['canal'].unique()
print("All unique channels in BASE DADOS.xlsx:")
for c in sorted(channels):
    v26 = df[df['canal'] == c]['venda_jul_26'].sum()
    print(f"  - {c!r:30s} -> Jul/26: R$ {v26:,.2f}")

digital_names = {'APP', 'APP TELE ENTREGA', 'E-COMMERCE', 'E_COMMERCE', 'IFOOD', 'SITE', 'SITE TELE ENTREGA', 'MERCADO LIVRE', 'PLATAFORMAS', 'WHATSAPP'}
tele_names = {'TELE ENCAMINHADA LOJAS', 'TELE VIZINHANÇA', 'TELE VIZINHANCA', 'VENDA TELE ENTREGA', 'VENDA TELE ENTREGA CENTRAL', 'TELEVENDAS', 'DELIVERY'}

df['is_digital'] = df['canal'].apply(lambda c: any(k in str(c).upper() for k in digital_names))
df['is_tele'] = df['canal'].apply(lambda c: any(k in str(c).upper() for k in tele_names))
df['is_dt'] = df['is_digital'] | df['is_tele']

v_total = df['venda_jul_26'].sum()
v_digital = df[df['is_digital']]['venda_jul_26'].sum()
v_dt = df[df['is_dt']]['venda_jul_26'].sum()
v_loja = df[~df['is_dt']]['venda_jul_26'].sum()

print("\n--- COMPILAÇÕES CANAIS (JUL/26) ---")
print(f"Venda Digital:        R$ {v_digital:,.2f} ({v_digital/v_total*100:.2f}%)")
print(f"Venda Digital + Tele: R$ {v_dt:,.2f} ({v_dt/v_total*100:.2f}%)")
print(f"Venda Loja Física:    R$ {v_loja:,.2f} ({v_loja/v_total*100:.2f}%)")
print(f"EMPRESA TOTAL:        R$ {v_total:,.2f} (100.00%)")
