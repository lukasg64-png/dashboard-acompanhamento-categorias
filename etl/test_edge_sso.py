import asyncio
from playwright.async_api import async_playwright

async def run():
    print("Testando Microsoft Edge SSO com Playwright...")
    async with async_playwright() as p:
        # Launch MS Edge
        browser = await p.chromium.launch(channel="msedge", headless=True, args=['--ignore-certificate-errors'])
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        app_url = "https://sense.farmaciassaojoao.com.br/sense/app/671fa4f4-eb7d-418f-b4c9-936e87d8011d"
        print(f"Navegando para: {app_url}...")
        
        response = await page.goto(app_url, timeout=30000)
        await page.wait_for_timeout(8000)
        
        print("Page URL final:", page.url)
        print("Page Title final:", await page.title())

        cookies = await context.cookies()
        print("Cookies salvos:", len(cookies))
        for c in cookies:
            print(f"  {c['name']} = {c['value'][:30]}...")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
