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
    print("  CONFIGURANDO PROTOCOLO HTTP PURO SEM TLS NO COOLIFY")
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

        # 2. Subpágina de Domínios
        await page.goto(DOMAINS_URL, timeout=30000)
        await page.wait_for_timeout(3000)

        # Dismiss popup
        maybe_btn = await page.query_selector('button:has-text("Maybe next time")')
        if maybe_btn:
            await maybe_btn.click(force=True)
            await page.wait_for_timeout(500)

        # Desativar Redirect HTTP to HTTPS se estiver ativo
        redirect_toggle = await page.query_selector('*:has-text("Redirect HTTP to HTTPS") ~ * button, button:has-text("Enabled")')
        if redirect_toggle:
            print("  Desativando Redirect HTTP to HTTPS...")
            await redirect_toggle.click(force=True)
            await page.wait_for_timeout(1000)

        # Excluir a entrada HTTPS se houver e deixar apenas HTTP
        delete_btns = await page.query_selector_all('button[title*="Delete"], svg[class*="trash"], button:has-text("Delete")')
        for dbtn in delete_btns:
            try:
                await dbtn.click(force=True)
                await page.wait_for_timeout(1000)
            except Exception:
                pass

        # Adicionar o domínio HTTP categorias.10.200.12.69.sslip.io
        add_btn = await page.wait_for_selector('button:has-text("Add")', timeout=5000)
        if add_btn:
            await add_btn.click(force=True)
            await page.wait_for_timeout(1000)

            # Selecionar http no protocolo
            proto_btn = await page.query_selector('div[role="dialog"] button:has-text("https"), button:has-text("https")')
            if proto_btn:
                await proto_btn.click(force=True)
                await page.wait_for_timeout(500)
                http_opt = await page.query_selector('button:has-text("http"), span:has-text("http")')
                if http_opt:
                    await http_opt.click(force=True)
                    await page.wait_for_timeout(500)

            domain_inp = await page.wait_for_selector('input[placeholder*="example"]', timeout=5000)
            if domain_inp:
                await domain_inp.fill("categorias.10.200.12.69.sslip.io")
                await page.wait_for_timeout(500)

            save_modal_btn = await page.query_selector('div[role="dialog"] button:has-text("Save"), button:has-text("Save")')
            if save_modal_btn:
                await save_modal_btn.click(force=True)
                await page.wait_for_timeout(2000)

            # Clicar no botão Continue via JS
            await page.evaluate('''() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const contBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Continue');
                if (contBtn) contBtn.click();
            }''')
            await page.wait_for_timeout(3000)

        # 3. Reiniciar a aplicação para aplicar as regras de roteamento HTTP
        await page.goto(APP_URL, timeout=30000)
        await page.wait_for_timeout(2000)

        actions_btn = await page.wait_for_selector('button:has-text("Actions")', timeout=10000)
        if actions_btn:
            await actions_btn.click(force=True)
            await page.wait_for_timeout(1000)

            restart_opt = await page.query_selector('div[role="menu"] *:has-text("Restart"), span:has-text("Restart")')
            if restart_opt:
                await restart_opt.click(force=True)
                print("   Restart disparado com sucesso!")
                await page.wait_for_timeout(6000)

        os.makedirs('logs', exist_ok=True)
        await page.screenshot(path='logs/coolify_http_domain_configured.png')
        print("  Screenshot final salvo em: logs/coolify_http_domain_configured.png")

        await browser.close()
        print("======================================================================")

if __name__ == "__main__":
    asyncio.run(main())
