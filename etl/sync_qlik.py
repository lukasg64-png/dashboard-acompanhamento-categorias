"""
sync_qlik.py — Sincronizador Completo Qlik Sense -> Dashboard Acompanhamento Categorias
1. Extrai dados vivos de Agosto (D-1) com fórmula oficial de Resultado Líquido do Qlik Sense Enterprise.
2. Mantém dados históricos de Julho fechados e consolidados.
3. Empacota ambos os meses no HTML autocontido ultracompacto (dist/index.html).
4. Publica no GitHub Gist CDN e comita/sobe no Gitea Corporativo (10.200.12.69).
"""
import os, sys, time, json, asyncio, subprocess, datetime

if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETL_DIR = os.path.join(BASE_DIR, 'etl')
DIST_FILE = os.path.join(BASE_DIR, 'dist', 'index.html')
GIST_ID_FILE = os.path.join(BASE_DIR, 'dist', '.gist_id')

def run_step(desc, script_name):
    print(f"\n{'='*70}")
    print(f"  {desc}")
    print(f"{'='*70}")
    script_path = os.path.join(ETL_DIR, script_name)
    res = subprocess.run([sys.executable, script_path], cwd=BASE_DIR)
    if res.returncode != 0:
        print(f"  ⚠️ Aviso na etapa {script_name}")

def push_to_gitea():
    print(f"\n{'='*70}")
    print("  4/5  SINCRONIZANDO COM GITEA (10.200.12.69)...")
    print(f"{'='*70}")
    try:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(['git', 'add', '.'], cwd=BASE_DIR, check=True)
        res_diff = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=BASE_DIR)
        if res_diff.returncode != 0:
            subprocess.run(['git', 'commit', '-m', f"Auto-sync Qlik Sense - {now_str}"], cwd=BASE_DIR, check=True)
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE_DIR, check=True)
            print(f"  ✅ Repositório Gitea atualizado com sucesso!")
        else:
            print("  [i] Nenhuma alteração pendente no repositório Git.")
    except Exception as e:
        print(f"  ⚠️ Aviso ao sincronizar com Gitea: {e}")

def publish_gist():
    print(f"\n{'='*70}")
    print("  5/5  PUBLICANDO NO GITHUB GIST CDN...")
    print(f"{'='*70}")
    try:
        gist_id = '7dfb809d825e40189203b2451d48d3c6'
        if os.path.exists(GIST_ID_FILE):
            with open(GIST_ID_FILE, 'r') as f:
                gist_id = f.read().strip()
                
        cmd = ['gh', 'gist', 'edit', gist_id, '--add', DIST_FILE]
        res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  ✅ Gist {gist_id} atualizado com sucesso!")
        else:
            print(f"  ⚠️ Aviso no Gist: {res.stderr}")
    except Exception as e:
        print(f"  ⚠️ Aviso ao publicar Gist: {e}")

def main():
    t0 = time.time()
    print("\n🚀 INICIANDO SINCRONIZAÇÃO AUTOMÁTICA QLIK SENSE -> DASHBOARD\n")
    
    # 1. Extração ao vivo do Qlik Sense (Agosto D-1)
    run_step("1/5  EXTRAINDO AGOSTO (D-1) DO QLIK SENSE...", "extract_complete_qlik_models.py")
    
    # 2. Processamento da Base de Julho
    run_step("2/5  PROCESSANDO BASE CONSOLIDADA DE JULHO...", "process_data.py")
    
    # 3. Gerar HTML autocontido com ambos os meses
    run_step("3/5  GERANDO HTML AUTOCONTIDO (JULHO + AGOSTO)...", "build_single_file.py")
    
    # 4. Gitea
    push_to_gitea()
    
    # 5. Gist CDN
    publish_gist()

    print("\n" + "=" * 70)
    print(f"  🎉 SINCRONIZAÇÃO COMPLETA CONCLUÍDA EM {time.time() - t0:.2f}s!")
    print("=" * 70)
    print("  🌐 Links Públicos e Acessíveis:")
    print("  - HTML Preview: https://htmlpreview.github.io/?https://gist.githubusercontent.com/lukasg64-png/7dfb809d825e40189203b2451d48d3c6/raw/index.html")
    print("  - Githack Raw:  https://gist.githack.com/lukasg64-png/7dfb809d825e40189203b2451d48d3c6/raw/index.html")
    print("  - Gitea Repo:   http://10.200.12.69/plan-Dados/dashboard-acompanhamento-categorias")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    main()
