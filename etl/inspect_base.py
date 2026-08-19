"""Inspect BASE DADOS.xlsx structure — columns, data types, date ranges, sample rows."""
import os, sys, tempfile
import pandas as pd

tmp = os.path.join(tempfile.gettempdir(), 'BASE_DADOS_temp.xlsx')

print("=" * 80)
print("LENDO BASE DADOS.xlsx...")
print("=" * 80)

# Read just first 50 rows to inspect structure quickly
df_sample = pd.read_excel(tmp, nrows=50)

print(f"\nShape (sample): {df_sample.shape}")
print(f"\nColunas ({len(df_sample.columns)}):")
for i, col in enumerate(df_sample.columns):
    dtype = df_sample[col].dtype
    sample_vals = df_sample[col].dropna().head(3).tolist()
    print(f"  [{i}] {col!r:40s}  dtype={dtype!s:15s}  ex: {sample_vals}")

print("\n" + "=" * 80)
print("PRIMEIRAS 10 LINHAS:")
print("=" * 80)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', 30)
print(df_sample.head(10).to_string())

print("\n" + "=" * 80)
print("ÚLTIMAS 5 LINHAS (da amostra):")
print("=" * 80)
print(df_sample.tail(5).to_string())

# Check for date columns
date_cols = [c for c in df_sample.columns if df_sample[c].dtype in ['datetime64[ns]', 'object'] 
             and any(kw in str(c).lower() for kw in ['data', 'date', 'dia', 'dt'])]
print(f"\nPossíveis colunas de data: {date_cols}")

# Try to get full date range info by reading just the date column
print("\n" + "=" * 80)
print("ANÁLISE DE DATAS (leitura completa da coluna de data)...")
print("=" * 80)

# Read with chunksize for efficiency - just get column names and date ranges
for col in df_sample.columns:
    if df_sample[col].dtype == 'datetime64[ns]' or 'data' in str(col).lower() or 'date' in str(col).lower() or 'dia' in str(col).lower():
        print(f"\n  Coluna: {col}")
        # Read just that column from full file
        try:
            full_col = pd.read_excel(tmp, usecols=[col])
            print(f"  Total rows: {len(full_col)}")
            print(f"  Dtype: {full_col[col].dtype}")
            unique = full_col[col].dropna().unique()
            print(f"  Valores únicos: {len(unique)}")
            if full_col[col].dtype == 'datetime64[ns]':
                print(f"  Min: {full_col[col].min()}")
                print(f"  Max: {full_col[col].max()}")
            else:
                print(f"  Primeiros 20 únicos: {sorted(unique)[:20]}")
        except Exception as e:
            print(f"  Erro: {e}")

print("\n\nTotal colunas:", len(df_sample.columns))
print("Nomes:", list(df_sample.columns))
