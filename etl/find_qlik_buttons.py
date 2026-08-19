import os, sys, asyncio, json
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

QLIK_URL = "https://sense.farmaciassaojoao.com.br"
APP_ID = "671fa4f4-eb7d-418f-b4c9-936e87d8011d"
SHEET_ID = "ddd70c77-1a06-40d9-aff2-efa4b6b67b24"
SHEET_URL = f"{QLIK_URL}/sense/app/{APP_ID}/sheet/{SHEET_ID}/state/analysis"

USERNAME = "lucas.alves6"
PASSWORD = "Eloise2025*"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={'username': USERNAME, 'password': PASSWORD},
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print("1. Conectando ao Qlik Sense...")
        await page.goto(SHEET_URL, timeout=60000)
        await page.wait_for_timeout(10000)
        
        # Mover mouse sobre a tabela
        await page.mouse.move(500, 300)
        await page.wait_for_timeout(2000)
        
        # Inspecionar todos os botões e ícones visíveis
        buttons = await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('button, [role="button"], .lui-icon, .qv-object-nav, .actions, [title]'));
            return btns.map(b => ({
                title: b.getAttribute('title') || b.getAttribute('aria-label') || b.innerText.trim(),
                className: b.className,
                tagName: b.tagName
            })).filter(x => x.title);
        }''')
        
        print("Botões encontrados na página:")
        for b in buttons:
            print(" ->", b)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
