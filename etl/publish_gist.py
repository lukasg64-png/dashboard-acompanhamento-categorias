"""
publish_gist.py — Publica o dashboard como GitHub Gist usando apenas urllib (sem gh CLI).
Uso: python publish_gist.py

Na primeira vez, ele vai pedir seu GitHub Personal Access Token.
Crie em: https://github.com/settings/tokens -> "Generate new token (classic)"
Marque apenas o escopo "gist" e gere o token.

O token fica salvo em ~/.dashboard_gist_token para uso futuro.
"""
import os
import json
import urllib.request
import urllib.error
import getpass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.basename(BASE) == 'etl':
    BASE = os.path.dirname(BASE)

DIST_FILE = os.path.join(BASE, 'dist', 'index.html')
TOKEN_FILE = os.path.join(os.path.expanduser('~'), '.dashboard_gist_token')
GIST_ID_FILE = os.path.join(BASE, 'dist', '.gist_id')

GIST_API = 'https://api.github.com/gists'


def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            token = f.read().strip()
            if token:
                return token

    print("\n" + "=" * 60)
    print("  CONFIGURAÇÃO DO GITHUB TOKEN (só precisa fazer 1 vez)")
    print("=" * 60)
    print("\n1. Acesse: https://github.com/settings/tokens")
    print("2. Clique em 'Generate new token (classic)'")
    print("3. Marque APENAS o escopo 'gist'")
    print("4. Gere e copie o token\n")

    token = getpass.getpass("Cole seu GitHub Token aqui: ").strip()
    if not token:
        print("Token vazio, abortando.")
        exit(1)

    with open(TOKEN_FILE, 'w') as f:
        f.write(token)
    print(f"Token salvo em {TOKEN_FILE}\n")
    return token


def get_existing_gist_id():
    if os.path.exists(GIST_ID_FILE):
        with open(GIST_ID_FILE, 'r') as f:
            return f.read().strip()
    return None


def save_gist_id(gist_id):
    with open(GIST_ID_FILE, 'w') as f:
        f.write(gist_id)


def publish():
    if not os.path.exists(DIST_FILE):
        print(f"[ERRO] Arquivo não encontrado: {DIST_FILE}")
        print("       Execute primeiro: python build_single_file.py")
        exit(1)

    with open(DIST_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    token = get_token()
    gist_id = get_existing_gist_id()

    payload = {
        "description": "Dashboard Acompanhamento de Categorias — Farmácias São João",
        "public": False,
        "files": {
            "index.html": {
                "content": content
            }
        }
    }

    data = json.dumps(payload).encode('utf-8')

    if gist_id:
        # Update existing gist
        url = f"{GIST_API}/{gist_id}"
        method = 'PATCH'
        print(f"Atualizando Gist existente: {gist_id}...")
    else:
        # Create new gist
        url = GIST_API
        method = 'POST'
        print("Criando novo Gist...")

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', f'token {token}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    req.add_header('User-Agent', 'DashboardPublisher/1.0')

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            new_id = result['id']
            html_url = result['html_url']

            save_gist_id(new_id)

            # Build the raw URL for direct browser access
            owner = result['owner']['login']
            raw_url = f"https://gist.githack.com/{owner}/{new_id}/raw/index.html"

            print("\n" + "=" * 60)
            print("  ✅ GIST PUBLICADO COM SUCESSO!")
            print("=" * 60)
            print(f"\n  📋 Gist URL:    {html_url}")
            print(f"  🌐 Abrir direto: {raw_url}")
            print(f"\n  Gist ID salvo em: {GIST_ID_FILE}")
            print("  (Próximas execuções vão ATUALIZAR este mesmo Gist)")
            print()

    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"\n[ERRO] HTTP {e.code}: {body}")
        if e.code == 401:
            print("Token inválido ou expirado. Delete o arquivo e tente novamente:")
            print(f"  del {TOKEN_FILE}")
        elif e.code == 422:
            print("Arquivo pode ser muito grande para o Gist (limite ~10 MB).")
        exit(1)


if __name__ == '__main__':
    publish()
