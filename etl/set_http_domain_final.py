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
    print("  CONFIGURACAO FINAL DOMINIO HTTP SEM REDIRECIONAMENTO E SEM POPUP")
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

        # Fechar qualquer modal via Javascript
        await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const maybe = btns.find(b => b.innerText && b.innerText.includes('Maybe next time'));
            if (maybe) maybe.click();
            
            // pressionar Escape
            document.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));
        }''')
        await page.wait_for_timeout(1000)

        # 1. Alterar 'Redirect HTTP to HTTPS' para 'Disabled' via JS
        print("  1. Alterando 'Redirect HTTP to HTTPS' para Disabled...")
        await page.evaluate('''() => {
            const select = document.querySelector('select');
            if (select) {
                select.value = 'false';
                select.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }''')
        await page.wait_for_timeout(1000)

        # 2. Deletar linhas antigas do domínio categorias
        print("  2. Deletando linhas de domínio antigas...")
        await page.evaluate('''() => {
            const rows = Array.from(document.querySelectorAll('tr'));
            rows.forEach(row => {
                if (row.innerText && row.innerText.includes('categorias')) {
                    const btns = Array.from(row.querySelectorAll('button'));
                    const lastBtn = btns[btns.length - 1];
                    if (lastBtn) lastBtn.click();
                }
            });
        }''')
        await page.wait_for_timeout(1500)

        # Confirmar exclusão se modal aparecer
        await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const conf = btns.find(b => b.innerText && (b.innerText.trim() === 'Confirm' || b.innerText.trim() === 'Remove domain'));
            if (conf) conf.click();
        }''')
        await page.wait_for_timeout(2000)

        # 3. Adicionar http://categorias.10.200.12.69.sslip.io
        print("  3. Adicionando http://categorias.10.200.12.69.sslip.io...")
        add_btn = await page.query_selector('button:has-text("Add")')
        if add_btn:
            await add_btn.click(force=True)
            await page.wait_for_timeout(1000)

            # Preencher protocolo e dominio
            await page.evaluate('''() => {
                const inputs = Array.from(document.querySelectorAll('input'));
                const domainInp = inputs.find(i => i.placeholder && i.placeholder.includes('example'));
                if (domainInp) {
                    domainInp.value = 'http://categorias.10.200.12.69.sslip.io';
                    domainInp.dispatchEvent(new Event('input', { bubbles: true }));
                    domainInp.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }''')
            await page.wait_for_timeout(500)

            # Clicar em Save
            await page.evaluate('''() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const save = btns.find(b => b.innerText && b.innerText.trim() === 'Save');
                if (save) save.click();
            }''')
            await page.wait_for_timeout(2000)

            # Clicar em Continue se houver alerta de DNS
            await page.evaluate('''() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const cont = btns.find(b => b.innerText && b.innerText.trim() === 'Continue');
                if (cont) cont.click();
            }''')
            await page.wait_for_timeout(2000)

        os.makedirs('logs', exist_ok=True)
        await page.screenshot(path='logs/coolify_final_domains.png')
        print("  Screenshot final salvo em: logs/coolify_final_domains.png")

        # 4. Trigger Redeploy
        await page.goto(APP_URL, timeout=30000)
        await page.wait_for_timeout(2000)

        actions_btn = await page.wait_for_selector('button:has-text("Actions")', timeout=10000)
        if actions_btn:
            await actions_btn.click(force=True)
            await page.wait_for_timeout(1000)

            redeploy_opt = await page.query_selector('div[role="menu"] *:has-text("Redeploy"), span:has-text("Redeploy"), *:has-text("Restart")')
            if redeploy_opt:
                await redeploy_opt.click(force=True)
                print("   Redeploy/Restart disparado com sucesso!")
                await page.wait_for_timeout(10000)

        await browser.close()
        print("======================================================================")

if __name__ == "__main__":
    asyncio.run(main())
