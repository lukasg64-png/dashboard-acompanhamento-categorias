import os, sys, asyncio
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1400, 'height': 900})
        page = await context.new_page()
        
        print("1. Login no Coolify...")
        await page.goto('http://10.200.12.69:8000/login')
        await page.fill('input[type="email"]', 'fsjplan.dados@gmail.com')
        await page.fill('input[type="password"]', 'ecommerce2026')
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        
        print("2. Acessando tela de criação de recurso...")
        await page.goto('http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/new')
        await page.wait_for_timeout(3000)
        
        # Encontrar e clicar no card de Private Git Repository
        # Vamos buscar pelo texto exato e clicar
        print("3. Procurando card 'Private Git Repository'...")
        private_git_card = page.locator('div:has-text("Private Git Repository (with Deploy Key)")').last
        # Clicar dentro do card ou no botão Deploy
        deploy_btn = private_git_card.locator('button').last
        await deploy_btn.click()
        await page.wait_for_timeout(3000)
        
        print("URL atual:", page.url)
        await page.screenshot(path='step1_deploy_clicked.png')
        
        text = await page.inner_text('body')
        print("Texto na tela:", text[:600].replace('\n', ' | '))

        # Verificar se pede servidor (localhost)
        server_option = page.locator('text=localhost, text=Default, text=Server').first
        if await server_option.is_visible():
            print("Clicando no servidor...")
            await server_option.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path='step2_server_clicked.png')

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
