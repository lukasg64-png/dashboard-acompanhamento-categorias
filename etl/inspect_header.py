"""Detailed inspection of BASE DADOS.xlsx headers and first few rows."""
import os, tempfile
import pandas as pd

tmp = os.path.join(tempfile.gettempdir(), 'BASE_DADOS_temp.xlsx')

# Copy if not exists or update
src = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\Acompanhamento Categorias\BASE DADOS.xlsx"
if os.path.exists(src):
    import shutil
    try:
        shutil.copy2(src, tmp)
    except Exception as e:
        print("Copy exception:", e)

df = pd.read_excel(tmp, nrows=5)
print("DF shape:", df.shape)
print("DF columns (first 20):", list(df.columns[:20]))
print("Row 0:", df.iloc[0].values[:20])
print("Row 1:", df.iloc[1].values[:20])
