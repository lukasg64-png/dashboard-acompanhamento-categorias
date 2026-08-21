import asyncio, os, sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

COOLIFY_URL = "http://10.200.12.69:8000"
USER_EMAIL = "fsjplan.dados@gmail.com"
USER_PASS = "ecommerce2026"
PROJECT_ENV_URL= "http://10.200.12.69:8000/project/e1otgbr9yumecg�<j15tl5qd/environment/br5vqn3kdkgvmvvhhbem5ayw"
GITEA_REPO_URL = "http://10.200.12.69/plan-Dados/dashboard-acompanhamento-categorias.git"

async def main():
    print("=" * 70)
    print("  CRIANDO NOVA APLICACAO NO COOLIFY")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1600, "height": 900})
        page = await context.new_page()

        print("  1. Executando login...")
        await page.goto(f"{COOLIFY_URL}/login", timeout=30000)
        await page.wait_for_selector('input[type="email"]', timeout=15000)
        await page.fill('input[type="email"]', USER_EMAIL)
        await page.fill('input[type="password"]', USER_PASS)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)

        print("  2. Acessando pagina de novo recurso...")
        await page.goto("http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvvhbem5ayw/new", timeout=30000)
        await page.wait_for_timeout(3000)

        # Listar todos os elementos interativos na pagina
        btn_texts = await page.eval_on_selector_all('button, a', 'elements => elements.map(e => ({tag: e.tagName, text: (e.innerText || "").trim(), href: e.href || "", wire: e.getAttribute("wire:click") || ""}))')
        print("  Elementos encontrados na pagina (max 30):")
        for e in btn_texts[:30]:
            if e['text'] or e['wire']:
                print(f"   -> {e['tag']} { e['text'] } | wire={e['wire']} | href={e['href']}")

        os.makedirs('logs', exist_ok=True)
        await page.screenshot(path='logs/coolify_new_resource.png')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())