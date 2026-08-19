"""
test_canal_group_linha.py — Test unique combinations of grupo, linha, canal
"""
import os, json
import pandas as pd

DATA_DIR = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\dashboard-acompanhamento-categorias\data"
DAILY_PARQUET = os.path.join(DATA_DIR, 'base_dados_daily.parquet')

df = pd.read_parquet(DAILY_PARQUET)

combos = df[['grupo', 'linha', 'canal']].drop_duplicates()
print(f"Unique (grupo, linha, canal) combinations: {len(combos)}")

dir_combos = df[['diretor', 'distrital', 'canal']].drop_duplicates()
print(f"Unique (diretor, distrital, canal) combinations: {len(dir_combos)}")
