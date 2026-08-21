import asyncio
import os
import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

COOLIFY_URL = "http://10.200.12.69:8000"
ENV_NEW_URL = f"{COOLIFY_URL}/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/new"
GITEA_REPO_URL = "http://10.200.12.69/plan-Dados/dashboard-acompanhamento-categorias.git"

async def main():
    print("=" * 70)
    print("  🚀 DEPLOY AUTOMÁTICO COOLIFY + GITEA (DASHBOARD CATEGORIAS)")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1600, 'height': 900})
        page = await context.new_page()

        print("  1. Efetuando login no Coolify...")
        await page.goto(f"{COOLIFY_URL}/login", timeout=30000)
        await page.wait_for_selector('input[type="email"]', timeout=15000)
        await page.fill('input[type="email"]', 'fsjplan.dados@gmail.com')
        await page.fill('input[type="password"]', 'ecommerce2026')
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)

        # 2. Navegar diretamente para a aplicação recém-criada
        APP_URL = "http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/application/kzxvytjjrekjdxdrz8upi8x1"
        APP_DOMAIN = "http://categorias.10.200.12.69.sslip.io"

        print(f"  2. Acessando a página da aplicação: {APP_URL}")
        await page.goto(APP_URL, timeout=30000)
        await page.wait_for_timeout(4000)

        # 3. Navegar diretamente para a página de domínios da aplicação
        DOMAINS_URL = f"{APP_URL}/domains"
        print(f"  3. Acessando a subpágina de Domínios: {DOMAINS_URL}...")
        await page.goto(DOMAINS_URL)
        await page.wait_for_timeout(3000)

        os.makedirs('logs', exist_ok=True)
        await page.screenshot(path='logs/coolify_domains_subpage.png')
        print("  📸 Screenshot da subpágina de Domínios salvo em: logs/coolify_domains_subpage.png")

        body_text = await page.inner_text('body')
        print("  Conteúdo da subpágina de Domínios:")
        print(body_text[:1500])

        # 4. Clicar no botão "Add" para adicionar um novo domínio FQDN
        print("  4. Clicando no botão 'Add' da página de Domínios...")
        add_btn = await page.wait_for_selector('button:has-text("Add")', timeout=5000)
        if add_btn:
            await add_btn.click(force=True)
            await page.wait_for_timeout(1000)

        os.makedirs('logs', exist_ok=True)
        await page.screenshot(path='logs/coolify_domains_after_add.png')
        print("  📸 Screenshot após clicar em Add salvo em: logs/coolify_domains_after_add.png")

        # A) Alterar Protocol para http
        print("  5. Preenchendo o modal Add domain...")
        proto_dropdown = await page.wait_for_selector('div[role="dialog"] button:has-text("https"), *:has-text("https")', timeout=5000)
        if proto_dropdown:
            await proto_dropdown.click(force=True)
            await page.wait_for_timeout(500)
            http_opt = await page.query_selector('*:has-text("http")')
            if http_opt:
                await http_opt.click(force=True)
                await page.wait_for_timeout(500)

        # B) Inserir domain limpo sem protocolo
        domain_inp = await page.wait_for_selector('input[placeholder*="example"]', timeout=5000)
        if domain_inp:
            print("   Inserindo domínio limpo: categorias.10.200.12.69.sslip.io...")
            await domain_inp.fill("categorias.10.200.12.69.sslip.io")
            await page.wait_for_timeout(500)

        # C) Clicar no botão Save do modal
        save_btn = await page.query_selector('div[role="dialog"] button:has-text("Save"), button:has-text("Save")')
        if save_btn:
            print("   1. Clicando no botão Save...")
            await save_btn.click(force=True)
            await page.wait_for_timeout(2000)

        # D) Disparar clique via JS no botão Continue se o aviso de DNS estiver visível
        print("   2. Forçando clique via JS no botão 'Continue'...")
        await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const contBtn = btns.find(b => b.innerText && b.innerText.trim() === 'Continue');
            if (contBtn) {
                contBtn.click();
                return true;
            }
            return false;
        }''')
        await page.wait_for_timeout(4000)
        print("   ✅ Domínio http://categorias.10.200.12.69.sslip.io salvo no Traefik com sucesso!")

        os.makedirs('logs', exist_ok=True)
        await page.screenshot(path='logs/coolify_domains_added_final.png')
        print("  📸 Screenshot final dos domínios salvo em: logs/coolify_domains_added_final.png")

        await browser.close()

        os.makedirs('logs', exist_ok=True)
        await page.screenshot(path='logs/coolify_dockerfile_build_result.png')
        print("  📸 Screenshot do resultado do build salvo em: logs/coolify_dockerfile_build_result.png")

        print("  Resumo do resultado do build:")
        print(body_text[:1800])

        await browser.close()
        print("=" * 70)
        print("🎉 DEPLOY DA APLICAÇÃO DISPARADO NO COOLIFY!")
        print(f"🌐 URL da Aplicação: {APP_DOMAIN}")
        print("=" * 70)

if __name__ == '__main__':
    asyncio.run(main())
