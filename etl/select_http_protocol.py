import asyncio
import os
from playwright.async_api import async_playwright

COOLIFY_URL = "http://10.200.12.69:8000"
COOLIFY_USER = "fsjplan.dados@gmail.com"
COOLIFY_PASS = "ecommerce2026"
APP_URL = f"{COOLIFY_URL}/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/application/kzxvytjjrekjdxdrz8upi8x1"
DOMAINS_URL = f"{APP_URL}/domains"

async def main():
    print("======================================================================")
    print("  SELECIONANDO PROTOCOLO HTTP NO DROPDOWN DO MODAL ADD DOMAIN")
    print("======================================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Login
        await page.goto(f"{COOLIFY_URL}/login")
        await page.wait_for_selector('input[type="email"]', timeout=10000)
        await page.fill('input[type="email"]', COOLIFY_USER)
        await page.fill('input[type="password"]', COOLIFY_PASS)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)

        # Domains subpage
        await page.goto(DOMAINS_URL, timeout=30000)
        await page.wait_for_timeout(3000)

        # Dismiss popups
        await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const closeNotif = btns.find(b => b.innerText && b.innerText.includes('Accept and close'));
            if (closeNotif) closeNotif.click();
            const maybe = btns.find(b => b.innerText && b.innerText.includes('Maybe next time'));
            if (maybe) maybe.click();
        }''')
        await page.wait_for_timeout(1000)

        # Clicar em + Add
        add_btn = await page.wait_for_selector('button:has-text("Add")', timeout=5000)
        if add_btn:
            await add_btn.click(force=True)
            await page.wait_for_timeout(1000)

            # Alterar protocolo de https para http usando teclado ou clique
            print("  Alterando dropdown Protocol de https para http...")
            proto_btn = await page.query_selector('div[role="dialog"] button:has-text("https"), div[role="dialog"] [role="combobox"]')
            if proto_btn:
                await proto_btn.click(force=True)
                await page.wait_for_timeout(500)
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(500)

            # Preencher domínio
            print("  Preenchendo domínio: categorias.10.200.12.69.sslip.io...")
            domain_inp = await page.wait_for_selector('input[placeholder*="example"]', timeout=5000)
            if domain_inp:
                await domain_inp.fill("categorias.10.200.12.69.sslip.io")
                await page.wait_for_timeout(500)

            # Clicar em Save
            save_btn = await page.query_selector('div[role="dialog"] button:has-text("Save")')
            if save_btn:
                await save_btn.click(force=True)
                print("   Save clicado!")
                await page.wait_for_timeout(3000)

            # Clicar em Continue se houver aviso de DNS
            await page.evaluate('''() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const cont = btns.find(b => b.innerText && b.innerText.trim() === 'Continue');
                if (cont) cont.click();
            }''')
            await page.wait_for_timeout(3000)

        os.makedirs('logs', exist_ok=True)
        await page.screenshot(path='logs/coolify_select_http_result.png')
        print("  Screenshot salvo em: logs/coolify_select_http_result.png")

        # Restart
        await page.goto(APP_URL, timeout=30000)
        await page.wait_for_timeout(2000)

        actions_btn = await page.wait_for_selector('button:has-text("Actions")', timeout=10000)
        if actions_btn:
            await actions_btn.click(force=True)
            await page.wait_for_timeout(1000)

            await page.evaluate('''() => {
                const btns = Array.from(document.querySelectorAll('button, div[role="menu"] *'));
                const restart = btns.find(b => b.innerText && b.innerText.trim() === 'Restart');
                if (restart) restart.click();
            }''')
            print("   Restart disparado!")
            await page.wait_for_timeout(5000)

        await browser.close()
        print("======================================================================")

if __name__ == "__main__":
    asyncio.run(main())
