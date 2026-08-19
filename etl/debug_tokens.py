import os, sys, asyncio
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('http://10.200.12.69:8000/login', timeout=15000)
        await page.fill('input[type="email"]', 'fsjplan.dados@gmail.com')
        await page.fill('input[type="password"]', 'ecommerce2026')
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(2000)
        
        await page.goto('http://10.200.12.69:8000/security/api-tokens', timeout=15000)
        await page.wait_for_timeout(2000)
        
        # Inspecionar inputs e botões
        inputs = await page.eval_on_selector_all('input', 'els => els.map(e => ({id: e.id, name: e.name, placeholder: e.placeholder}))')
        buttons = await page.eval_on_selector_all('button', 'els => els.map(e => ({text: e.innerText.trim(), wire: e.getAttribute("wire:click")}))')
        
        print("Inputs:", inputs)
        print("Buttons:", [b for b in buttons if b['text']])
        
        # Preencher input de token
        for inp in inputs:
            if inp['id'] or inp['name'] or inp['placeholder']:
                sel = f"#{inp['id']}" if inp['id'] else f"input[name='{inp['name']}']" if inp['name'] else "input"
                await page.fill(sel, 'AntigravityToken')
                print(f"Preencheu {sel}")
                break
                
        # Clicar no botão de criar token
        create_btn = await page.query_selector('button[type="submit"], button:has-text("Create"), button:has-text("Add New")')
        if create_btn:
            print("Clicando no botão de criar token...")
            await create_btn.click()
            await page.wait_for_timeout(3000)
            
        text = await page.inner_text('body')
        for line in text.split('\n'):
            if any(k in line.lower() for k in ['token', 'api', 'created', 'secret', 'antigravity']):
                print("Line:", line.strip())

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
