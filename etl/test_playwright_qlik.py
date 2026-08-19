import asyncio
from playwright.async_api import async_playwright

async def run():
    print("Iniciando Playwright para conectar ao Qlik Sense...")
    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        app_url = "https://sense.farmaciassaojoao.com.br/sense/app/671fa4f4-eb7d-418f-b4c9-936e87d8011d"
        print(f"Navegando para: {app_url}...")
        
        response = await page.goto(app_url, timeout=30000)
        print("Page URL:", page.url)

        # Check if redirected to login page
        if "login" in page.url or "internal_forms" in page.url:
            print("Página de login detectada. Preenchendo credenciais...")
            await page.fill('input[name="username"]', 'lucas.alves6')
            await page.fill('input[name="pwd"]', 'Eloise2025*')
            await page.click('input[type="submit"]')
            await page.wait_for_load_state('networkidle', timeout=15000)
            print("Login submetido! URL atual:", page.url)

        cookies = await context.cookies()
        print("Cookies capturados:", len(cookies))
        for c in cookies:
            if 'qlik' in c['name'].lower() or 'session' in c['name'].lower():
                print(f"  {c['name']} = {c['value'][:30]}...")

        # Wait for app layout to render
        await page.wait_for_timeout(5000)
        title = await page.title()
        print("Page Title:", title)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
