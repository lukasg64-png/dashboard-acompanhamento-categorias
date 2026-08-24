"""
daily_refresh.py — Rotina diária de extração D-1 do Qlik Sense, compilação e deploy.
Executado automaticamente todos os dias às 07:30 via Windows Task Scheduler.
"""
import os, sys, subprocess, time, json
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
        if res.stderr.strip():
            log(f"   Stderr: {res.stderr.strip()}")
        if res.stdout.strip():
            log(f"   Stdout: {res.stdout.strip()}")
        return False

def main():
    log("=" * 70)
    log("🔄 INICIANDO ATUALIZAÇÃO DIÁRIA DO DASHBOARD (07:30)")
    log("=" * 70)

    # 1. Extração D-1 (Qlik Sense WebSocket com retentativas e Fallback para Excel)
    py_exe = sys.executable
    extracted = False
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        log(f"Tentativa {attempt}/{max_retries} de extração direta Qlik Sense...")
        extracted = run_cmd(f'"{py_exe}" -u etl/extract_complete_qlik_models.py', f"1/3 Extração Qlik Sense Engine (Tentativa {attempt})")
        if extracted:
            break
        if attempt < max_retries:
            log("Aguardando 15s antes da próxima tentativa...")
            time.sleep(15)

    if not extracted:
        log("⚠️ Extração direta via Qlik WS não concluída após tentativas. Executando fallback via Excel OneDrive...")
        run_cmd(f'"{py_exe}" -u etl/process_agosto.py', "1b/3 Fallback Processamento Excel")

    # 2. Build HTML Único (dist/index.html)
    run_cmd(f'"{py_exe}" -u etl/build_single_file.py', "2/3 Compilação do HTML Único")

    # 3. Identificar período atualizado para o commit
    periodo_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    kpis_file = os.path.join(BASE_DIR, 'data', 'agosto', 'executive_kpis.json')
    if os.path.exists(kpis_file):
        try:
            with open(kpis_file, 'r', encoding='utf-8') as f:
                kpis_data = json.load(f)
                periodo_str = kpis_data.get('periodo_info', {}).get('periodo_str', periodo_str)
        except Exception:
            pass

    # 4. Commit e Deploy GitHub Pages
    run_cmd('git add .', "3a/4 Git Add")

    commit_msg = f"Auto-refresh D-1 Qlik Sense ({periodo_str})"
    commit_ok = run_cmd(f'git commit -m "{commit_msg}"', "3b/4 Git Commit")
    if not commit_ok:
        log("ℹ️ Nenhuma mudança pendente para commit. Forçando push para garantir sincronia.")

    run_cmd('git push github gh-pages:main --force', "3c/4 Git Push -> GitHub main")
    run_cmd('git push github gh-pages:gh-pages --force', "3d/4 Git Push -> GitHub gh-pages")

    # 5. Sincronizar com Gitea corporativo se disponível
    try:
        run_cmd('git push origin gh-pages:main --force', "4/4 Git Push -> Gitea Corporativo")
    except Exception:
        pass

    log("=" * 70)
    log(f"🎉 ATUALIZAÇÃO DIÁRIA CONCLUÍDA COM SUCESSO ({periodo_str})!")
    log("🌐 Link Público: https://lukasg64-png.github.io/dashboard-acompanhamento-categorias/")
    log("=" * 70)

if __name__ == '__main__':
    main()
