"""
daily_refresh.py — Rotina diária de extração D-1 do Qlik Sense, compilação e deploy.
Executado automaticamente todos os dias às 07:30 via Windows Task Scheduler.
"""
import os, sys, subprocess, time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'daily_refresh.log')

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"[{ts}] {msg}"
    print(entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

def run_cmd(cmd, step_name):
    log(f"Iniciando: {step_name} -> {cmd}")
    t0 = time.time()
    res = subprocess.run(cmd, shell=True, cwd=BASE_DIR, capture_output=True, text=True, encoding='utf-8', errors='replace')
    elapsed = time.time() - t0
    if res.returncode == 0:
        log(f"✅ {step_name} concluído com sucesso em {elapsed:.2f}s!")
        if res.stdout.strip():
            log(f"   Output: {res.stdout.strip().splitlines()[-1]}")
        return True
    else:
        log(f"❌ ERRO em {step_name} (code {res.returncode}):")
        log(f"   Stderr: {res.stderr.strip()}")
        log(f"   Stdout: {res.stdout.strip()}")
        return False

def main():
    log("=" * 70)
    log("🔄 INICIANDO ATUALIZAÇÃO DIÁRIA DO DASHBOARD (07:30)")
    log("=" * 70)

    # 1. Extração D-1 Qlik Sense
    py_exe = sys.executable
    if not run_cmd(f'"{py_exe}" etl/extract_complete_qlik_models.py', "1/4 Extração Qlik Sense Engine"):
        log("❌ Falha na extração. Abortando deploy.")
        return

    # 2. Build HTML Único
    if not run_cmd(f'"{py_exe}" etl/build_single_file.py', "2/4 Compilação do HTML Único"):
        log("❌ Falha no build. Abortando deploy.")
        return

    # 3. Commit e Push Gitea
    run_cmd('git add . && git commit -m "Auto-refresh D-1 (Daily 07:30)" && git push origin main', "3/4 Deploy Gitea Corporativo")

    # 4. Deploy GitHub Pages
    deploy_gh = (
        'git checkout -B gh-pages && '
        'cp dist/index.html index.html && '
        'git add index.html && '
        'git commit -m "Auto-deploy GitHub Pages (Daily 07:30)" && '
        'git push github gh-pages --force && '
        'git checkout main'
    )
    run_cmd(deploy_gh, "4/4 Deploy GitHub Pages Global")

    log("=" * 70)
    log("🎉 ATUALIZAÇÃO DIÁRIA CONCLUÍDA COM SUCESSO!")
    log("🌐 Link Público: https://lukasg64-png.github.io/dashboard-acompanhamento-categorias/")
    log("=" * 70)

if __name__ == '__main__':
    main()
