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
        
        # Check Private Keys
        await page.goto('http://10.200.12.69:8000/security/private-key')
        await page.wait_for_timeout(3000)
        keys = await page.eval_on_selector_all('a', 'elements => elements.map(e => ({href: e.href, text: e.innerText.trim()}))')
        print("Keys:", keys)

        # Let's inspect sources (like Gitea source if any)
        await page.goto('http://10.200.12.69:8000/sources')
        await page.wait_for_timeout(3000)
        sources = await page.eval_on_selector_all('a', 'elements => elements.map(e => ({href: e.href, text: e.innerText.trim()}))')
        print("Sources:", sources)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
