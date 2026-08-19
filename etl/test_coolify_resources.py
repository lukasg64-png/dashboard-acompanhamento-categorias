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
        
        # Check Project My first project
        await page.goto('http://10.200.12.69:8000/project/e1otgbr9yumecgjxj15tl5qd/environment/br5vqn3kdkgvmvbvhbem5ayw')
        await page.wait_for_timeout(3000)
        links = await page.eval_on_selector_all('a', 'elements => elements.map(e => ({href: e.href, text: e.innerText.trim()}))')
        print("Recursos em My first project:", [l for l in links if l['text']])

        # Check Project Infraestrutura
        await page.goto('http://10.200.12.69:8000/project/u2nbxywezf8dsscc0cdnyfsu/environment/szroka9hws7bwu5kstfcld8n')
        await page.wait_for_timeout(3000)
        links_infra = await page.eval_on_selector_all('a', 'elements => elements.map(e => ({href: e.href, text: e.innerText.trim()}))')
        print("Recursos em Infraestrutura:", [l for l in links_infra if l['text']])

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
