import asyncio, os, sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

COOLIFY_URL = "http://10.200.12.69:8000"
USER_EMAIL = "fsjplan.dados@gmail.com"
USER_PASS = "ecommerce2026"
PROJECT_ENV_URL = "http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw"
GITEA_REPO_URL = "http://10.200.12.69/plan-Dados/dashboard-acompanhamento-categorias.git"

async def main():
    print("=" * 70)
    print("  INICIANDO AUTOMACAO NO COOLIFY / GITEA")
    print("=" * 70)

    async with async_playwright() as p:
        print("  1. Abrindo navegador headless...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1600, "height": 900})
        page = await context.new_page()

        print(f"  2. Efetuando login em {COOLIFY_URL}...")
        await page.goto(f"{COOLIFY_URL}/login", timeout=30000)
        await page.wait_for_selector('input[type="email"]', timeout=15000)
        await page.fill('input[type="email"]', USER_EMAIL)
        await page.fill('input[type="password"]', USER_PASS)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)

        print("  3. Acessando ambiente de producao...")
        await page.goto(PROJECT_ENV_URL, timeout=30000)
        await page.wait_for_timeout(3000)

        links = await page.eval_on_selector_all('a', 'elements => elements.map(e => ({href: e.href, text: e.innerText.trim()}))')
        cat_app = next((l for l in links if 'Categorias' in l['text'] or 'categorias' in l['href']), None)

        if cat_app:
            print(f"  📌 Aplicacao existente encontrada: {cat_app['text']} ({cat_app['href']})")
            await page.goto(cat_app['href'], timeout=30000)
            await page.wait_for_timeout(3000)
        else:
            print("  📌 Lista de aplicacoes no ambiente:")
            for l in links:
                if '/application/' in l['href']:
                    print(f"   -> {l['text']}: {l['href']}")

        print("  4. Procurando botao de Deploy...")
        deploy_btn = await page.query_selector('button:has-text("Deploy"), button:has-text("Force Deploy"), button:has-text("Re-deploy")')
        if deploy_btn:
            btn_text = await deploy_btn.inner_text()
            print(f"  ✅ Botao de Deploy encontrado: '{btn_text.strip()}'")
            await deploy_btn.click()
            await page.wait_for_timeout(5000)
            print("  🚀 Comando de Deploy acionado no Coolify!")
        else:
            all_btns = await page.eval_on_selector_all('button', 'elements => elements.map(e => e.innerText.trim())')
            print(f"  Botoes na pagina: {all_btns}")

        os.makedirs('logs', exist_ok=True)
        screenshot_path = 'logs/coolify_deploy_status.png'
        await page.screenshot(path=screenshot_path)
        print(f"  📸 Captura salva em: {screenshot_path}")

        await browser.close()
        print("=" * 70)
        print("  PROCESSO DE DEPLOY CONCLUIDO NO COOLIFY!")
        print("=" * 70)

if __name__ == '__main__':
    asyncio.run(main())