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
        
        print("2. Hover na tabela do Qlik...")
        # Hover no centro da tela
        await page.mouse.move(500, 500)
        await page.wait_for_timeout(2000)
        
        # Clicar com botão direito na tabela
        print("3. Clicando com botão direito para abrir menu de contexto...")
        await page.mouse.click(500, 500, button='right')
        await page.wait_for_timeout(2000)
        
        # Inspecionar itens do menu de contexto
        menu_items = await page.evaluate('''() => {
            const items = Array.from(document.querySelectorAll('.lui-list__item, .qv-context-menu-item, [role="menuitem"], li, button'));
            return items.map(el => el.innerText.trim()).filter(t => t && t.length < 50);
        }''')
        
        print("Itens do menu de contexto:")
        print(menu_items[:20])
        
        await page.screenshot(path='qlik_context_menu.png')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
