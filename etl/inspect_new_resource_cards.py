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
        
        # Click on Applications
        # Let's find all clickable cards
        cards = await page.eval_on_selector_all('.card, button, a', 'elements => elements.map(e => ({text: e.innerText.trim(), tag: e.tagName, class: e.className})).filter(x => x.text)')
        print("Cards na tela:")
        for c in cards:
            if any(k in c['text'].lower() for k in ['private', 'public', 'git', 'application', 'docker']):
                print(" ->", c)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
