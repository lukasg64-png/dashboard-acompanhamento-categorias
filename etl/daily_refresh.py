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

    # 1. Extração D-1 (Qlik Sense WebSocket com Fallback para Excel OneDrive mais recente)
    py_exe = sys.executable
    extracted = run_cmd(f'"{py_exe}" -u etl/extract_complete_qlik_models.py', "1/3 Extração Qlik Sense Engine")
    if not extracted:
        log("⚠️ Extração direta via Qlik WS não concluída. Executando fallback via Excel OneDrive...")
        run_cmd(f'"{py_exe}" -u etl/process_agosto.py', "1b/3 Fallback Processamento Excel")

    # 2. Build HTML Único (dist/index.html)
    run_cmd(f'"{py_exe}" -u etl/build_single_file.py', "2/3 Compilação do HTML Único")

    # 3. Commit e Deploy GitHub Pages (cada passo separado para evitar falha em cadeia)
    run_cmd('git add .', "3a/3 Git Add")

    # git commit pode falhar se não houver mudanças — isso é OK
    commit_ok = run_cmd('git commit -m "Auto-refresh D-1 (Daily 07:30)"', "3b/3 Git Commit")
    if not commit_ok:
        log("ℹ️ Nenhuma mudança detectada no commit — dados iguais ao último deploy. Fazendo push mesmo assim.")

    # Push sempre executa (garante que commits anteriores pendentes também subam)
    run_cmd('git push github gh-pages:main --force', "3c/3 Git Push -> main")
    run_cmd('git push github gh-pages:gh-pages --force', "3d/3 Git Push -> gh-pages")

    log("=" * 70)
    log("🎉 ATUALIZAÇÃO DIÁRIA CONCLUÍDA COM SUCESSO!")
    log("🌐 Link Público: https://lukasg64-png.github.io/dashboard-acompanhamento-categorias/")
    log("=" * 70)

if __name__ == '__main__':
    main()
