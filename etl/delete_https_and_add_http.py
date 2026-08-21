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
    print("  REMOVENDO ENTRADA HTTPS E CONFIGURANDO HTTP PURO PARA CATEGORIAS")
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

        # Ir para Domains subpage
        await page.goto(DOMAINS_URL, timeout=30000)
        await page.wait_for_timeout(3000)

        # Dismiss popup
        maybe_btn = await page.query_selector('button:has-text("Maybe next time")')
        if maybe_btn:
            await maybe_btn.click(force=True)
            await page.wait_for_timeout(500)

        # 1. Clicar no botão da lixeira na linha do domínio categorias via JS
        print("  1. Clicando no botão de lixeira da linha categorias via JS...")
        await page.evaluate('''() => {
            const rows = Array.from(document.querySelectorAll('tr, div[class*="table"] tr'));
            const catRow = rows.find(r => r.innerText && r.innerText.includes('categorias'));
            if (catRow) {
                const btns = Array.from(catRow.querySelectorAll('button'));
                if (btns.length > 0) {
                    btns[btns.length - 1].click();
                }
            }
        }''')
        await page.wait_for_timeout(2000)

        # Se surgir modal de confirmação de exclusão via JS
        await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const conf = btns.find(b => b.innerText && (b.innerText.trim() === 'Confirm' || b.innerText.trim() === 'Delete' || b.innerText.trim() === 'Remove domain'));
            if (conf) conf.click();
        }''')
        await page.wait_for_timeout(2000)

        os.makedirs('logs', exist_ok=True)
        await page.screenshot(path='logs/coolify_after_delete_https.png')
        print("  Screenshot após deletar HTTPS salvo em: logs/coolify_after_delete_https.png")

        # 2. Adicionar http://categorias.10.200.12.69.sslip.io
        print("  2. Clicando em Add domain...")
        add_btn = await page.wait_for_selector('button:has-text("Add")', timeout=5000)
        if add_btn:
            await add_btn.click(force=True)
            await page.wait_for_timeout(1000)

            # Alterar dropdown Protocol de https para http
            # No modal, o primeiro listbox/dropdown tem opções https e http
            proto_box = await page.query_selector('div[role="dialog"] *:has-text("https")')
            if proto_box:
                await proto_box.click(force=True)
                await page.wait_for_timeout(500)
                http_item = await page.query_selector('div[role="dialog"] *:has-text("http"), button:has-text("http")')
                if http_item:
                    await http_item.click(force=True)
                    await page.wait_for_timeout(500)

            domain_inp = await page.wait_for_selector('input[placeholder*="example"]', timeout=5000)
            if domain_inp:
                await domain_inp.fill("categorias.10.200.12.69.sslip.io")
                print("   Domain input preenchido com: categorias.10.200.12.69.sslip.io")

            save_btn = await page.query_selector('div[role="dialog"] button:has-text("Save")')
            if save_btn:
                await save_btn.click(force=True)
                await page.wait_for_timeout(2000)

            # Confirmar Continue via JS
            await page.evaluate('''() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const contBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Continue');
                if (contBtn) contBtn.click();
            }''')
            await page.wait_for_timeout(3000)

        # 3. Reiniciar a aplicação
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

        await browser.close()
        print("======================================================================")

if __name__ == "__main__":
    asyncio.run(main())
