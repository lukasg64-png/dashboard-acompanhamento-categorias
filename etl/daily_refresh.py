"""
daily_refresh.py — Rotina diária de extração D-1 do Qlik Sense, compilação e deploy.
Executado automaticamente todos os dias às 07:30 via Windows Task Scheduler.
"""
import os, sys, subprocess, time, json, socket
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'daily_refresh.log')

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"[{ts}] {msg}"
    print(entry)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(entry + '\n')
    except Exception:
        pass

def acquire_single_instance_lock():
    """Garante que apenas uma instância da rotina seja executada por vez."""
    lock_file_path = os.path.join(LOG_DIR, '.daily_refresh.lock')
    try:
        f = open(lock_file_path, 'a+')
        import msvcrt
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        return f
    except Exception:
        log("⚠️ Outra instância do daily_refresh.py já está em execução. Encerrando esta para evitar concorrência.")
        sys.exit(0)

def clean_stale_git_lock():
    """Remove trava residual do Git caso tenha sobrado de processos anteriores."""
    lock_path = os.path.join(BASE_DIR, '.git', 'index.lock')
    if os.path.exists(lock_path):
        try:
            os.remove(lock_path)
            log("🧹 Arquivo de trava residual '.git/index.lock' removido com sucesso.")
        except Exception as e:
            log(f"⚠️ Aviso ao limpar .git/index.lock: {e}")

def run_cmd(cmd, step_name, timeout=300, retries=1, retry_delay=3):
    for attempt in range(1, retries + 1):
        log(f"Iniciando: {step_name} -> {cmd}")
        t0 = time.time()
        try:
            res = subprocess.run(
                cmd, shell=True, cwd=BASE_DIR,
                capture_output=True, text=True,
                encoding='utf-8', errors='replace',
                timeout=timeout
            )
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
                
                # Se for erro 128 (possível index.lock), limpa trava e tenta novamente
                if res.returncode == 128 and attempt < retries:
                    clean_stale_git_lock()
                    time.sleep(retry_delay)
                    continue
                if attempt < retries:
                    time.sleep(retry_delay)
                    continue
                return False
        except subprocess.TimeoutExpired:
            log(f"⏱️ TIMEOUT ({timeout}s) em {step_name}")
            return False
        except Exception as e:
            log(f"❌ Exceção em {step_name}: {e}")
            return False
    return False

def wait_for_qlik_network(host="sense.farmaciassaojoao.com.br", port=443, max_wait_seconds=300):
    """Aguarda até 5 minutos pela conectividade com o Qlik Sense (VPN/Rede Corporativa)."""
    log(f"Verificando conectividade com o Qlik Sense ({host}:{port})...")
    start = time.time()
    attempt = 1
    while time.time() - start < max_wait_seconds:
        try:
            with socket.create_connection((host, port), timeout=4):
                elapsed = time.time() - start
                if elapsed > 2:
                    log(f"🌐 Conexão com Qlik Sense estabelecida após {elapsed:.1f}s!")
                else:
                    log(f"🌐 Conexão com Qlik Sense OK!")
                return True
        except Exception:
            remaining = int(max_wait_seconds - (time.time() - start))
            if attempt % 3 == 0 or attempt == 1:
                log(f"⏳ Aguardando conexão de rede/VPN com {host} (restam ~{remaining}s)...")
            time.sleep(10)
            attempt += 1
    log(f"⚠️ Não foi possível conectar ao Qlik Sense ({host}) dentro do tempo limite ({max_wait_seconds}s).")
    return False

def main():
    _lock_handle = acquire_single_instance_lock()

    log("=" * 70)
    log("🔄 INICIANDO ATUALIZAÇÃO DIÁRIA DO DASHBOARD (07:30)")
    log("=" * 70)

    py_exe = sys.executable
    extract_script = os.path.join(BASE_DIR, 'etl', 'extract_complete_qlik_models.py')
    fallback_script = os.path.join(BASE_DIR, 'etl', 'process_agosto.py')
    build_script = os.path.join(BASE_DIR, 'etl', 'build_single_file.py')

    # 1. Verificar conexão de rede com Qlik Sense
    qlik_online = wait_for_qlik_network(max_wait_seconds=180)

    # 2. Extração D-1 (Qlik Sense WebSocket com retentativas e Fallback para Excel)
    extracted = False
    if qlik_online:
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            log(f"Tentativa {attempt}/{max_retries} de extração direta Qlik Sense...")
            extracted = run_cmd(f'"{py_exe}" -u "{extract_script}"', f"1/3 Extração Qlik Sense Engine (Tentativa {attempt})", timeout=600)
            if extracted:
                break
            if attempt < max_retries:
                log("Aguardando 15s antes da próxima tentativa...")
                time.sleep(15)

    if not extracted:
        log("⚠️ Extração direta via Qlik WS não concluída. Executando fallback via Excel OneDrive...")
        run_cmd(f'"{py_exe}" -u "{fallback_script}"', "1b/3 Fallback Processamento Excel", timeout=600)

    # 3. Build HTML Único (dist/index.html e index.html raiz)
    run_cmd(f'"{py_exe}" -u "{build_script}"', "2/3 Compilação do HTML Único", timeout=300)

    # 4. Identificar período atualizado para o commit
    periodo_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    kpis_file = os.path.join(BASE_DIR, 'data', 'agosto', 'executive_kpis.json')
    if os.path.exists(kpis_file):
        try:
            with open(kpis_file, 'r', encoding='utf-8') as f:
                kpis_data = json.load(f)
                periodo_str = kpis_data.get('periodo_info', {}).get('periodo_str', periodo_str)
        except Exception:
            pass

    # 5. Commit e Deploy GitHub Pages
    clean_stale_git_lock()
    run_cmd('git add .', "3a/4 Git Add", timeout=60, retries=3, retry_delay=2)

    commit_msg = f"Auto-refresh D-1 Qlik Sense ({periodo_str})"
    commit_ok = run_cmd(f'git commit -m "{commit_msg}"', "3b/4 Git Commit", timeout=60, retries=2, retry_delay=2)
    if not commit_ok:
        log("ℹ️ Nenhuma mudança pendente para commit. Forçando push para garantir sincronia.")

    run_cmd('git push github HEAD:main --force', "3c/4 Git Push -> GitHub main", timeout=180, retries=2, retry_delay=3)
    run_cmd('git push github HEAD:gh-pages --force', "3d/4 Git Push -> GitHub gh-pages", timeout=180, retries=2, retry_delay=3)

    # 6. Sincronizar com Gitea corporativo se disponível
    try:
        run_cmd('git push origin HEAD:main --force', "4/4 Git Push -> Gitea Corporativo", timeout=120, retries=2, retry_delay=3)
    except Exception:
        pass

    log("=" * 70)
    log(f"🎉 ATUALIZAÇÃO DIÁRIA CONCLUÍDA COM SUCESSO ({periodo_str})!")
    log("🌐 Link Público: https://lukasg64-png.github.io/dashboard-acompanhamento-categorias/")
    log("=" * 70)

if __name__ == '__main__':
    main()

