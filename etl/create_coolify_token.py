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
        
        # Ir para API Tokens
        await page.goto('http://10.200.12.69:8000/security/api-tokens')
        await page.wait_for_timeout(3000)
        
        # Preencher nome do token e criar
        inputs = await page.query_selector_all('input')
        for inp in inputs:
            p_holder = await inp.get_attribute('placeholder') or ''
            name = await inp.get_attribute('name') or ''
            if 'token' in p_holder.lower() or 'name' in name.lower() or 'name' in p_holder.lower():
                await inp.fill('Antigravity-Sync-Token')
                break
        
        # Clicar em Criar / Add / Save
        save_btn = await page.query_selector('button:has-text("Create"), button:has-text("Add"), button:has-text("Save"), button:has-text("Novo")')
        if save_btn:
            await save_btn.click()
            await page.wait_for_timeout(3000)
            
        # Obter o token gerado da página
        text = await page.inner_text('body')
        print("Texto na página de Tokens:")
        print(text[:1000])

        await page.screenshot(path='coolify_tokens.png')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
