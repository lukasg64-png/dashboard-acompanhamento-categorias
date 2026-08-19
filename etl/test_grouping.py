"""
test_grouping.py — Test grouping by grupo, subgrupo, linha only for hierarquia_detalhada
"""
import os, json
import pandas as pd

DATA_DIR = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\dashboard-acompanhamento-categorias\data"
DAILY_PARQUET = os.path.join(DATA_DIR, 'base_dados_daily.parquet')

df = pd.read_parquet(DAILY_PARQUET)

unique_lines = df[['grupo', 'subgrupo', 'linha']].drop_duplicates()
print(f"Unique (grupo, subgrupo, linha) combinations: {len(unique_lines)}")

date_cols = [c for c in df.columns if c.endswith('/2025') or c.endswith('/2026')]
print(f"Total date columns: {len(date_cols)}")
