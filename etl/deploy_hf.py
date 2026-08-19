"""
deploy_hf.py — Publica o dashboard no Hugging Face Spaces (Estático, 24/7 online em qualquer computador).
Uso: python etl/deploy_hf.py
"""
import os, sys, shutil, tempfile, subprocess, urllib.request, json

if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_FILE = os.path.join(BASE_DIR, 'dist', 'index.html')
TOKEN = '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'
USER = 'lukasg64-png'
SPACE_NAME = 'dashboard-acompanhamento-categorias'
REMOTE_URL = f"https://{USER}:{TOKEN}@huggingface.co/spaces/{USER}/{SPACE_NAME}"

def ensure_space_exists():
    url = 'https://huggingface.co/api/repos/create'
    payload = json.dumps({
        'name': SPACE_NAME,
        'type': 'space',
        'sdk': 'static',
        'private': False
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    })
    try:
        urllib.request.urlopen(req)
        print(f"Space '{SPACE_NAME}' verificado/criado com sucesso.")
    except Exception:
        pass

def deploy():
    if not os.path.exists(DIST_FILE):
        print(f"[ERRO] Arquivo não encontrado: {DIST_FILE}")
        sys.exit(1)

    print("Garantindo repositório no Hugging Face...")
    ensure_space_exists()

    print("Preparando arquivos para publicação...")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy dist/index.html to tmpdir/index.html
        shutil.copy(DIST_FILE, os.path.join(tmpdir, 'index.html'))
        
        # Create README.md
        readme = """---
title: Dashboard Acompanhamento Categorias
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: static
pinned: false
---
"""
        with open(os.path.join(tmpdir, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme)

        subprocess.run(['git', 'init'], cwd=tmpdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'config', 'user.name', 'Lucas Alves'], cwd=tmpdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'config', 'user.email', 'lucas.alves@farmaciassaojoao.com.br'], cwd=tmpdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'add', '.'], cwd=tmpdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'commit', '-m', 'Deploy Dashboard'], cwd=tmpdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'remote', 'add', 'origin', REMOTE_URL], cwd=tmpdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("Enviando código para a nuvem Hugging Face...")
        res = subprocess.run(['git', '-c', 'http.sslVerify=false', 'push', 'origin', 'master:main', '--force'], cwd=tmpdir)
        
        if res.returncode == 0:
            direct_url = f"https://{USER}-{SPACE_NAME}.hf.space"
            space_url = f"https://huggingface.co/spaces/{USER}/{SPACE_NAME}"
            print("\n" + "=" * 70)
            print("  ✅ DASHBOARD PUBLICADO NO HUGGING FACE COM SUCESSO!")
            print("=" * 70)
            print(f"\n  🌐 LINK DIRETO (Acessível de qualquer PC/Celular fora da rede):")
            print(f"     {direct_url}")
            print(f"\n  📋 Página do Space:")
            print(f"     {space_url}")
            print("\n" + "=" * 70 + "\n")
            return direct_url
        else:
            print("[ERRO] Falha ao fazer push para o Hugging Face Space.")
            sys.exit(1)

if __name__ == '__main__':
    deploy()
