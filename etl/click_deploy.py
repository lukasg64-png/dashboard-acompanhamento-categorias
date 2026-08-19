import os, sys, asyncio
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('http://10.200.12.69:8000/login')
        await page.wait_for_selector('input[type="email"]')
        await page.fill('input[type="email"]', 'fsjplan.dados@gmail.com')
        await page.fill('input[type="password"]', 'ecommerce2026')
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        
        await page.goto('http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/new')
        await page.wait_for_timeout(3000)
        
        # Encontrar todos os botões Deploy
        # Procurar o elemento que tem o texto 'Private Git Repository'
        card = page.locator('div:has-text("Private Git Repository (with Deploy Key)")').last
        deploy_btn = card.locator('button:has-text("Deploy"), a:has-text("Deploy")').first
        print("Clicando no botão Deploy...")
        await deploy_btn.click()
        await page.wait_for_timeout(4000)
        
        print("URL após clique:", page.url)
        text = await page.inner_text('body')
        for line in text.split('\n'):
            if any(k in line.lower() for k in ['step', 'server', 'destination', 'repository', 'private key', 'continue']):
                print("Line:", line.strip())

        await page.screenshot(path='coolify_after_deploy_click.png')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
