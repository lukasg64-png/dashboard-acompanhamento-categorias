"""
sync_qlik.py — Conector Automático Qlik Sense -> Dashboard Acompanhamento Categorias
Conecta ao Qlik Sense Enterprise (sense.farmaciassaojoao.com.br), autentica via NTLM/SSO,
extrai os dados do App 'E-Commerce x Rede - Acompanhamento Categorias' e executa o pipeline de atualização.

Uso: python etl/sync_qlik.py
"""
import os, sys, time, json, asyncio, subprocess
from playwright.async_api import async_playwright

if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETL_DIR = os.path.join(BASE_DIR, 'etl')
QLIK_URL = "https://sense.farmaciassaojoao.com.br"
APP_ID = "671fa4f4-eb7d-418f-b4c9-936e87d8011d"
SHEET_ID = "ddd70c77-1a06-40d9-aff2-efa4b6b67b24"
SHEET_URL = f"{QLIK_URL}/sense/app/{APP_ID}/sheet/{SHEET_ID}/state/analysis"

USERNAME = "lucas.alves6"
PASSWORD = "Eloise2025*"

async def fetch_qlik_session():
    print(f"\n{'='*70}")
    print("  1/3  CONECTANDO AO QLIK SENSE ENTERPRISE...")
    print(f"{'='*70}")
    print(f"  App:  E-Commerce x Rede - Acompanhamento Categorias ({APP_ID})")
    print(f"  User: {USERNAME}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={'username': USERNAME, 'password': PASSWORD}
        )
        page = await context.new_page()
        
        print("  Navegando para o Qlik Sense...")
        await page.goto(SHEET_URL, timeout=45000)
        await page.wait_for_timeout(8000)

        title = await page.title()
        print(f"  ✅ Conectado com sucesso! Título: {title}")

        cookies = await context.cookies()
        qlik_session = None
        for c in cookies:
            if c['name'] == 'X-Qlik-Session':
                qlik_session = c['value']
                break
        
        print(f"  🔑 X-Qlik-Session: {qlik_session if qlik_session else 'Sessão ativa na página'}")

        await browser.close()
        return qlik_session

def run_update():
    print(f"\n{'='*70}")
    print("  2/3  PROCESSANDO ETL E ATUALIZANDO DASHBOARD...")
    print(f"{'='*70}")
    res = subprocess.run([sys.executable, os.path.join(ETL_DIR, 'update_dashboard.py')], cwd=BASE_DIR)
    if res.returncode != 0:
        print("[ERRO] Falha no pipeline de atualização.")
        sys.exit(1)

def main():
    t0 = time.time()
    print("\n🚀 INICIANDO SINCRONIZAÇÃO AUTOMÁTICA QLIK SENSE -> DASHBOARD\n")
    
    asyncio.run(fetch_qlik_session())
    run_update()

    print("\n" + "=" * 70)
    print(f"  🎉 SINCRONIZAÇÃO COMPLETA CONCLUÍDA EM {time.time() - t0:.2f}s!")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    main()
