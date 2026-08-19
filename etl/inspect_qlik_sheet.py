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
        
        print("2. Título da página:", await page.title())
        
        # Inspecionar objetos do Qlik na página
        # Qlik Sense usa tags como .qv-object, .qv-inner-object, qv-grid-cell, etc.
        objects = await page.evaluate('''() => {
            const objs = Array.from(document.querySelectorAll('.qv-object, [data-qvid], .qv-grid-cell'));
            return objs.map(el => {
                const title = el.querySelector('.qv-object-title, header, h1, h2, h3, h4')?.innerText || '';
                const qvid = el.getAttribute('data-qvid') || el.id || '';
                const type = el.getAttribute('aria-label') || el.className || '';
                return { qvid, title: title.trim(), type: type.slice(0, 80) };
            }).filter(o => o.title || o.qvid);
        }''')
        
        print(f"3. Encontrados {len(objects)} objetos na pasta:")
        for obj in objects:
            print(" ->", obj)

        # Inspecionar todas as pastas/sheets do App
        sheets = await page.evaluate('''() => {
            // Tentar encontrar links de pastas ou menu
            const list = Array.from(document.querySelectorAll('.qv-sheet-list-item, [role="listitem"]'));
            return list.map(l => l.innerText.trim()).filter(Boolean);
        }''')
        print("Pastas encontradas:", sheets)

        # Capturar screenshot
        await page.screenshot(path='qlik_sheet_analysis.png')
        print("Screenshot salvo em qlik_sheet_analysis.png")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
