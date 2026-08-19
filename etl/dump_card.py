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
        
        card_info = await page.evaluate('''() => {
            const divs = Array.from(document.querySelectorAll('div, a, button'));
            const match = divs.filter(d => d.innerText && d.innerText.includes('Private Git Repository'));
            return match.map(m => ({
                tag: m.tagName,
                text: m.innerText.slice(0, 100),
                attributes: Array.from(m.attributes).map(a => `${a.name}="${a.value}"`)
            }));
        }''')
        
        for c in card_info[:10]:
            print("---", c['tag'], c['text'].replace('\n', ' '))
            print("   ", c['attributes'])

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
