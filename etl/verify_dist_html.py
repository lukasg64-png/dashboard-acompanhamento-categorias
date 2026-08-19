import os, sys, asyncio, json
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = f"file:///{os.path.join(BASE_DIR, 'dist', 'index.html').replace(os.sep, '/')}"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        errors = []
        page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        
        print("Abrindo dist/index.html...")
        await page.goto(INDEX_PATH)
        await page.wait_for_timeout(3000)
        
        # Testar renderização de KPIs e linhas da tabela
        kpi_text = await page.locator('#kpiStrip').inner_text()
        tbody_canais = await page.locator('#tbodyCanais').inner_html()
        tbody_cats = await page.locator('#tbodyCategorias').inner_html()
        
        print("Status dos KPIs:")
        print(kpi_text[:300] if kpi_text else "[VAZIO]")
        print(f"Linhas em Canais: {tbody_canais.count('<tr')}")
        print(f"Linhas em Categorias: {tbody_cats.count('<tr')}")
        
        if errors:
            print("❌ Erros de console encontrados:")
            for e in errors: print("  ", e)
        else:
            print("✅ Zero erros de JavaScript!")
            
        await page.screenshot(path="dashboard_agosto_verified.png")
        print("📸 Screenshot salvo em dashboard_agosto_verified.png")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
