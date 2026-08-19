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
        
        # Inspecionar app Acompanhamento de Cupons Source
        await page.goto('http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/application/nkxwwkscrggatkblx0gwqvx9/source')
        await page.wait_for_timeout(3000)
        text = await page.inner_text('body')
        for line in text.split('\n'):
            if any(k in line.lower() for k in ['git', 'ssh', 'http', 'repo', 'branch', 'key', 'gitea']):
                print("Source line:", line.strip())

        # Inspecionar todas as tabs
        links = await page.eval_on_selector_all('a', 'elements => elements.map(e => ({href: e.href, text: e.innerText.trim()}))')
        print("Links na app:", [l for l in links if '/application/nkxwwkscrggatkblx0gwqvx9' in l['href']])

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
