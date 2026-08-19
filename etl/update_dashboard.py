"""
update_dashboard.py — Pipeline completo de atualização do Dashboard com suporte a datas.
Uso: python update_dashboard.py
"""
import os, sys, time, subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETL_DIR = os.path.join(BASE_DIR, 'etl')
DATA_DIR = os.path.join(BASE_DIR, 'data')

DAILY_PARQUET = os.path.join(DATA_DIR, 'base_dados_daily.parquet')
EXCEL_PATH = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\Acompanhamento Categorias\BASE DADOS.xlsx"
DIST_FILE = os.path.join(BASE_DIR, 'dist', 'index.html')
GIST_ID_FILE = os.path.join(BASE_DIR, 'dist', '.gist_id')

def run_step(label, cmd, cwd=None):
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    res = subprocess.run(cmd, cwd=cwd or ETL_DIR)
    if res.returncode != 0:
        print(f"\n[ERRO] Falha no passo: {label}")
        sys.exit(1)

def main():
    t0 = time.time()
    print("\n🚀 ATUALIZANDO DASHBOARD ACOMPANHAMENTO DE CATEGORIAS (COM DATAS)\n")

    need_parse = False
    if not os.path.exists(DAILY_PARQUET):
        need_parse = True
    elif os.path.exists(EXCEL_PATH):
        if os.path.getmtime(EXCEL_PATH) > os.path.getmtime(DAILY_PARQUET):
            need_parse = True

    if need_parse:
        run_step("1/4  Processando datas diárias do Excel (build_daily_dataset.py)...",
                 [sys.executable, os.path.join(ETL_DIR, 'build_daily_dataset.py')])
    else:
        print("  [i] Cache Parquet diário atualizado. Pulando parse do Excel.")

    run_step("2/4  Gerando resumos JSON com vetores diários (process_data.py)...",
             [sys.executable, os.path.join(ETL_DIR, 'process_data.py')])

    run_step("3/4  Gerando HTML autocontido (build_single_file.py)...",
             [sys.executable, os.path.join(ETL_DIR, 'build_single_file.py')])

    if not os.path.exists(GIST_ID_FILE):
        cmd = ['gh', 'gist', 'create', DIST_FILE,
               '--desc', 'Dashboard Acompanhamento de Categorias — Farmácias São João',
               '--public']
    else:
        with open(GIST_ID_FILE, 'r') as f:
            gist_id = f.read().strip()
        print(f"\n  Atualizando Gist existente: {gist_id}")
        cmd = ['gh', 'gist', 'edit', gist_id, '--add', DIST_FILE]

    run_step("4/4  Publicando no GitHub Gist...", cmd, cwd=BASE_DIR)

    gist_id = ''
    if os.path.exists(GIST_ID_FILE):
        with open(GIST_ID_FILE, 'r') as f:
            gist_id = f.read().strip()

    print("\n" + "=" * 70)
    print(f"  ✅ DASHBOARD ATUALIZADO E PUBLICADO EM {time.time() - t0:.2f}s!")
    print("=" * 70)
    print(f"\n  📋 Gist GitHub:    https://gist.github.com/lukasg64-png/{gist_id}")
    print(f"  🌐 HTML Preview:   https://htmlpreview.github.io/?https://gist.githubusercontent.com/lukasg64-png/{gist_id}/raw/index.html")
    print(f"  ⚡ Githack Raw:    https://gist.githack.com/lukasg64-png/{gist_id}/raw/index.html")
    print(f"\n  📂 Arquivo Local:  {DIST_FILE}")
    print()

if __name__ == '__main__':
    main()
