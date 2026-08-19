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
        
        await page.goto('http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw/new')
        await page.wait_for_timeout(3000)
        
        # Get HTML of all elements containing 'Private Git'
        html_cards = await page.evaluate('''() => {
            const elements = Array.from(document.querySelectorAll('div, a, button, section'));
            return elements
                .filter(e => e.innerText && e.innerText.includes('Private Git Repository'))
                .map(e => ({tag: e.tagName, html: e.outerHTML.slice(0, 500)}));
        }''')
        
        print("HTML Cards:")
        for c in html_cards[:5]:
            print("---", c['tag'])
            print(c['html'])

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
