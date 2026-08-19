"""Inspect Base Parcial agosto - deeper structure analysis."""
import os, shutil, tempfile
import pandas as pd

src = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\Acompanhamento Categorias\Base Parcial agosto de 01 a 17 .xlsx"
tmp = os.path.join(tempfile.gettempdir(), 'BASE_AGOSTO_temp.xlsx')
shutil.copy2(src, tmp)

# Read first 10 rows including headers
df_raw = pd.read_excel(tmp, header=None, nrows=10)
print("="*80)
print("RAW HEADERS (sem header parse) - primeiras 10 linhas x primeiras 15 cols:")
print("="*80)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)
pd.set_option('display.max_colwidth', 25)
print(df_raw.iloc[:, :15].to_string())

print("\n\nRAW HEADERS - colunas 15 a 30:")
if df_raw.shape[1] > 15:
    print(df_raw.iloc[:, 15:30].to_string())

print("\n\nRAW HEADERS - colunas 30 a 53:")
if df_raw.shape[1] > 30:
    print(df_raw.iloc[:, 30:53].to_string())

print("\n" + "="*80)
print("RESUMO DA ESTRUTURA:")
print("="*80)
print(f"Total colunas: {df_raw.shape[1]}")
print(f"Linha 0 (header canais): {list(df_raw.iloc[0, :])}")
print(f"Linha 1 (sub-header): {list(df_raw.iloc[1, :])}")
print(f"Linha 2 (dados inicio): {list(df_raw.iloc[2, :])}")

# Now read properly with correct header
df = pd.read_excel(tmp, nrows=20)
print(f"\nShape com header auto: {df.shape}")
print(f"Colunas: {list(df.columns)}")

# Show sample data rows
print("\n" + "="*80)
print("PRIMEIRAS 5 LINHAS DE DADOS:")
print("="*80)
for i in range(min(5, len(df))):
    row = df.iloc[i]
    vals = {c: row[c] for c in df.columns[:15]}
    print(f"  Row {i}: {vals}")
