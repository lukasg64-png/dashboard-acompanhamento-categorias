import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("1. Logando no Coolify...")
        await page.goto('http://10.200.12.69:8000/login')
        await page.wait_for_selector('input[type="email"]')
        await page.fill('input[type="email"]', 'fsjplan.dados@gmail.com')
        await page.fill('input[type="password"]', 'ecommerce2026')
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        
        print("2. Acessando página de Novo Recurso...")
        await page.goto('http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/new')
        await page.wait_for_timeout(3000)
        
        # Encontrar o card de Private Git Repository e clicar em Deploy
        buttons = await page.query_selector_all('button')
        deploy_clicked = False
        for btn in buttons:
            txt = await btn.inner_text()
            # Encontrar o botão Deploy mais próximo
            parent_text = await (await btn.evaluate_handle('el => el.closest("div") ? el.closest("div").innerText : ""')).json_value()
            if 'deploy' in txt.lower() and 'private git' in parent_text.lower():
                print(f"Clicando em deploy no card: {parent_text[:60]}...")
                await btn.click()
                deploy_clicked = True
                break
        
        if not deploy_clicked:
            # Tentar clicar pelo texto
            print("Tentando clicar no botão Deploy de Private Git...")
            deploy_buttons = await page.query_selector_all('button:has-text("Deploy")')
            if len(deploy_buttons) >= 2:
                # O segundo costuma ser Private Git
                await deploy_buttons[1].click()
        
        await page.wait_for_timeout(3000)
        print("URL após clique em Deploy:", page.url)
        
        text = await page.inner_text('body')
        print("Texto na página de criação de app:")
        print(text[:1000])

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
