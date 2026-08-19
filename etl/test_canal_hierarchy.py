"""
test_canal_hierarchy.py — Test channel breakdown with product hierarchy
"""
import os, json
import pandas as pd

DATA_DIR = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\dashboard-acompanhamento-categorias\data"
DAILY_PARQUET = os.path.join(DATA_DIR, 'base_dados_daily.parquet')

df = pd.read_parquet(DAILY_PARQUET)

unique_combos = df[['grupo', 'subgrupo', 'linha', 'canal']].drop_duplicates()
print(f"Unique (grupo, subgrupo, linha, canal) combinations: {len(unique_combos)}")
