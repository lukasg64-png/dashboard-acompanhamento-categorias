import asyncio
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
        
        # Inspecionar app Acompanhamento de Cupons
        await page.goto('http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/application/nkxwwkscrggatkblx0gwqvx9')
        await page.wait_for_timeout(4000)
        
        inputs = await page.eval_on_selector_all('input, select, textarea', '''elements => elements.map(e => ({
            name: e.name || e.id || e.placeholder,
            value: e.value,
            type: e.type
        }))''')
        print("Campos da aplicação Acompanhamento de Cupons:")
        for inp in inputs:
            if inp['value']:
                print(" ->", inp)
                
        text = await page.inner_text('body')
        for line in text.split('\n'):
            if any(k in line.lower() for k in ['git', 'repository', 'branch', 'port', 'domain', 'build', 'dockerfile', 'sslip.io']):
                print("Text line:", line.strip())

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
