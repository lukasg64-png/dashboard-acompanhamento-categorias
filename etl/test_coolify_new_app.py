import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Login no Coolify...")
        await page.goto('http://10.200.12.69:8000/login')
        await page.wait_for_selector('input[type="email"]')
        await page.fill('input[type="email"]', 'fsjplan.dados@gmail.com')
        await page.fill('input[type="password"]', 'ecommerce2026')
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        
        # Ir para New Resource
        await page.goto('http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/new')
        await page.wait_for_timeout(3000)
        
        # Listar opções de New Resource
        buttons = await page.eval_on_selector_all('button, a', 'elements => elements.map(e => ({text: e.innerText.trim(), href: e.href || ""})).filter(x => x.text)')
        print("Opções na tela de Novo Recurso:")
        for b in buttons:
            if any(k in b['text'].lower() for k in ['git', 'application', 'docker', 'public', 'private', 'deploy']):
                print(" ->", b)
        
        await page.screenshot(path='coolify_new_resource.png')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
