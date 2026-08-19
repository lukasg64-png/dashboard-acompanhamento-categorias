"""Script to parse BASE DADOS.xlsx structure completely, map dates, and save as Parquet."""
import os, sys, time, tempfile
import pandas as pd
import numpy as np

tmp = os.path.join(tempfile.gettempdir(), 'BASE_DADOS_temp.xlsx')
src = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\Acompanhamento Categorias\BASE DADOS.xlsx"
if os.path.exists(src):
    import shutil
    try:
        shutil.copy2(src, tmp)
    except Exception as e:
        print("Copy error:", e)

t0 = time.time()
print("Reading Excel...")
# Read raw dataframe without header (header=None)
df_raw = pd.read_excel(tmp, header=None)
print(f"Excel read in {time.time() - t0:.2f}s. Raw shape: {df_raw.shape}")

# Row 0 has dates (for cols >= 9) and column names for cols 0..8
# Row 1 has sub-headers: 'Desc_Grupo', 'Desc_Subgrupo', ..., 'Canal', 'Resultado Líquido', 'Valor Desconto', ...
print("Row 0 cols 0..15:", df_raw.iloc[0, :15].tolist())
print("Row 1 cols 0..15:", df_raw.iloc[1, :15].tolist())
