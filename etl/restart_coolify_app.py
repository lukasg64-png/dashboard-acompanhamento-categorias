import asyncio
import os
from playwright.async_api import async_playwright

COOLIFY_URL = "http://10.200.12.69:8000"
COOLIFY_USER = "fsjplan.dados@gmail.com"
COOLIFY_PASS = "ecommerce2026"
APP_URL = f"{COOLIFY_URL}/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/application/kzxvytjjrekjdxdrz8upi8x1"

async def main():
    print("======================================================================")
    print("  REINICIANDO APLICACAO NO COOLIFY PARA APLICAR NOVO DOMINIO")
    print("======================================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Login
        await page.goto(f"{COOLIFY_URL}/login")
        await page.wait_for_selector('input[type="email"]', timeout=10000)
        await page.fill('input[type="email"]', COOLIFY_USER)
        await page.fill('input[type="password"]', COOLIFY_PASS)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)

        # 2. Ir para a página da aplicação
        await page.goto(APP_URL, timeout=30000)
        await page.wait_for_timeout(3000)

        # 3. Dismiss popup se houver
        maybe_btn = await page.query_selector('button:has-text("Maybe next time")')
        if maybe_btn:
            await maybe_btn.click(force=True)
            await page.wait_for_timeout(500)

        # 4. Clicar em Actions -> Restart
        print("  Clicando em Actions -> Restart...")
        actions_btn = await page.wait_for_selector('button:has-text("Actions")', timeout=10000)
        if actions_btn:
            await actions_btn.click(force=True)
            await page.wait_for_timeout(1000)

            restart_opt = await page.query_selector('div[role="menu"] *:has-text("Restart"), span:has-text("Restart")')
            if restart_opt:
                await restart_opt.click(force=True)
                print("   Comando Restart enviado com sucesso!")
                await page.wait_for_timeout(10000)

        os.makedirs('logs', exist_ok=True)
        await page.screenshot(path='logs/coolify_after_restart.png')
        print("  Screenshot pos-restart salvo em: logs/coolify_after_restart.png")

        await browser.close()
        print("======================================================================")

if __name__ == "__main__":
    asyncio.run(main())
