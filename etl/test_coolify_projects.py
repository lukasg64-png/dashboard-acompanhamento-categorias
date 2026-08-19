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
        
        # Check projects
        await page.goto('http://10.200.12.69:8000/projects')
        await page.wait_for_timeout(2000)
        links = await page.eval_on_selector_all('a', 'elements => elements.map(e => ({href: e.href, text: e.innerText}))')
        print("Projetos:", [l for l in links if '/project/' in l['href']])

        # Check sources
        await page.goto('http://10.200.12.69:8000/sources')
        await page.wait_for_timeout(2000)
        text_sources = await page.inner_text('body')
        print("Fontes/Sources:", text_sources[:400])

        # Check servers
        await page.goto('http://10.200.12.69:8000/servers')
        await page.wait_for_timeout(2000)
        text_servers = await page.inner_text('body')
        print("Servidores:", text_servers[:400])

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
