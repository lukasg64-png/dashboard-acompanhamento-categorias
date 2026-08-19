import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Acessando tela de login...")
        await page.goto('http://10.200.12.69:8000/login')
        await page.wait_for_selector('input[name="email"], input[type="email"]')
        await page.fill('input[name="email"], input[type="email"]', 'fsjplan.dados@gmail.com')
        await page.fill('input[name="password"], input[type="password"]', 'ecommerce2026')
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(4000)
        print("URL após login:", page.url)
        
        # Obter texto da página
        text = await page.inner_text('body')
        print("Texto da tela:", text[:500])
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
