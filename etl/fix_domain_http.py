import asyncio
from playwright.async_api import async_playwright

COOLIFY_URL = "http://10.200.12.69:8000"
COOLIFY_USER = "fsjplan.dados@gmail.com"
COOLIFY_PASS = "ecommerce2026"
APP_URL = f"{COOLIFY_URL}/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/application/kzxvytjjrekjdxdrz8upi8x1"

async def main():
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
        await page.goto(f"{APP_URL}/domains", timeout=30000)
        await page.wait_for_timeout(3000)

        # Dismiss popup
        maybe_btn = await page.query_selector('button:has-text("Maybe next time")')
        if maybe_btn:
            await maybe_btn.click(force=True)
            await page.wait_for_timeout(500)

        # Inspecionar o botão de Redirect HTTP to HTTPS
        print("1. Inspecionando o toggle 'Redirect HTTP to HTTPS'...")
        toggles = await page.query_selector_all('input[type="checkbox"], button[role="switch"], div:has-text("Redirect HTTP to HTTPS") ~ * button')
        print(f"  Toggles encontrados: {len(toggles)}")
        for idx, t in enumerate(toggles):
            try:
                print(f"   Toggle #{idx}: innerText='{await t.inner_text()}'")
                await t.click(force=True)
                await page.wait_for_timeout(1000)
            except Exception as e:
                print(f"   Erro no toggle #{idx}: {e}")

        # Inspecionar botões de exclusão na tabela de domínios
        print("2. Procurando botão para remover a entrada HTTPS de categorias...")
        trash_btns = await page.query_selector_all('tr:has-text("categorias") button, tr:has-text("categorias") svg')
        print(f"  Elementos na linha categorias: {len(trash_btns)}")
        for idx, tb in enumerate(trash_btns):
            try:
                await tb.click(force=True)
                await page.wait_for_timeout(1000)
            except Exception as e:
                pass

        # Adicionar novo domínio com HTTP puro via Add
        print("3. Clicando em Add domain...")
        add_btn = await page.wait_for_selector('button:has-text("Add")', timeout=5000)
        if add_btn:
            await add_btn.click(force=True)
            await page.wait_for_timeout(1000)

            # Mudar dropdown Protocol de https para http
            # O dropdown de protocolo é o primeiro select ou button no modal dialog
            select_proto = await page.query_selector('div[role="dialog"] select, select[x-model*="protocol"]')
            if select_proto:
                await select_proto.select_option("http")
                print("   Protocolo 'http' selecionado no <select>!")
            else:
                proto_btn = await page.query_selector('div[role="dialog"] button:has-text("https")')
                if proto_btn:
                    await proto_btn.click(force=True)
                    await page.wait_for_timeout(300)
                    http_opt = await page.query_selector('button:has-text("http"), span:has-text("http")')
                    if http_opt:
                        await http_opt.click(force=True)
                        print("   Protocolo 'http' selecionado no dropdown customizado!")

            domain_inp = await page.wait_for_selector('input[placeholder*="example"]', timeout=5000)
            if domain_inp:
                await domain_inp.fill("categorias.10.200.12.69.sslip.io")
                print("   Preenchido categorias.10.200.12.69.sslip.io!")

            save_modal = await page.query_selector('div[role="dialog"] button:has-text("Save")')
            if save_modal:
                await save_modal.click(force=True)
                await page.wait_for_timeout(2000)

            # Confirmar Continue se o aviso de DNS surgir
            await page.evaluate('''() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const contBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Continue');
                if (contBtn) contBtn.click();
            }''')
            await page.wait_for_timeout(3000)

        # Clicar em Deploy para aplicar todas as novas rotas Traefik
        await page.goto(APP_URL, timeout=30000)
        await page.wait_for_timeout(2000)

        actions_btn = await page.wait_for_selector('button:has-text("Actions")', timeout=10000)
        if actions_btn:
            await actions_btn.click(force=True)
            await page.wait_for_timeout(1000)

            deploy_opt = await page.query_selector('div[role="menu"] *:has-text("Deploy"), span:has-text("Deploy")')
            if deploy_opt:
                await deploy_opt.click(force=True)
                print("   Disparando RE-DEPLOY para recarregar Traefik!")
                await page.wait_for_timeout(15000)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
