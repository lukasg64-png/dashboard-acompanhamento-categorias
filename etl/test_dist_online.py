import os, sys, asyncio, json
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

BASE_URL_FILE = "file:///C:/Users/lucas.alves6/OneDrive%20-%20Farm%C3%A1cias%20S%C3%A3o%20Jo%C3%A3o/Documentos/ANTIGRAVITI/dashboard-acompanhamento-categorias/dist/index.html"
BASE_URL_GITHACK = "https://gist.githack.com/lukasg64-png/7dfb809d825e40189203b2451d48d3c6/raw/index.html"

async def test_page(url_name, url):
    print(f"\n==========================================")
    print(f"Testando {url_name}: {url}")
    print(f"==========================================")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        errors = []
        page.on("pageerror", lambda e: errors.append(f"PAGE_ERROR: {str(e)}"))
        page.on("console", lambda m: errors.append(f"CONSOLE_{m.type.upper()}: {m.text}") if m.type in ['error', 'warning'] else None)
        
        try:
            resp = await page.goto(url, timeout=30000)
            print(f"HTTP Status: {resp.status if resp else 'file'}")
            await page.wait_for_timeout(4000)
            
            period_text = await page.evaluate("() => document.getElementById('refPeriodoText')?.textContent || document.getElementById('refPeriodo')?.textContent || 'N/A'")
            kpis_rendered = await page.evaluate("() => document.querySelectorAll('.apple-kpi-card').length")
            print(f"Texto do Período: '{period_text}'")
            print(f"Qtd KPI Cards Renderizados: {kpis_rendered}")
            
            if errors:
                print("\n⚠️ Erros capturados no console:")
                for err in errors[:10]:
                    print("  ", err)
            else:
                print("✅ Nenhum erro no console!")
                
        except Exception as ex:
            print(f"❌ Exceção ao carregar página: {ex}")
            
        await browser.close()

async def main():
    await test_page("LOCAL DIST FILE", BASE_URL_FILE)
    await test_page("ONLINE GITHACK LINK", BASE_URL_GITHACK)

if __name__ == '__main__':
    asyncio.run(main())
