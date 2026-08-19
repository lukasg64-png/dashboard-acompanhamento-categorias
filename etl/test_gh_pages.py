import os, sys, asyncio, json, time
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

GH_PAGES_URL = "https://lukasg64-png.github.io/dashboard-acompanhamento-categorias/"

async def test_gh_pages():
    print(f"\n==========================================")
    print(f"Testando GITHUB PAGES: {GH_PAGES_URL}")
    print(f"==========================================")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        errors = []
        page.on("pageerror", lambda e: errors.append(f"PAGE_ERROR: {str(e)}"))
        page.on("console", lambda m: errors.append(f"CONSOLE_{m.type.upper()}: {m.text}") if m.type in ['error', 'warning'] else None)
        
        for attempt in range(10):
            try:
                resp = await page.goto(GH_PAGES_URL, timeout=30000)
                status = resp.status if resp else 0
                print(f"Tentativa {attempt+1} - HTTP Status: {status}")
                if status == 200:
                    await page.wait_for_timeout(4000)
                    period_text = await page.evaluate("() => document.getElementById('refPeriodoText')?.textContent || document.getElementById('refPeriodo')?.textContent || 'N/A'")
                    kpis_count = await page.evaluate("() => document.querySelectorAll('.apple-kpi-card').length")
                    print(f"  Texto do Período: '{period_text}'")
                    print(f"  Qtd KPI Cards Renderizados: {kpis_count}")
                    
                    if kpis_count >= 6 and "Agosto" in period_text:
                        print("  ✅ DASHBOARD CARREGADO COM SUCESSO NO GITHUB PAGES!")
                        if errors:
                            print("  ⚠️ Avisos no console:", errors)
                        else:
                            print("  ✅ Nenhum erro no console!")
                        break
                await asyncio.sleep(5)
            except Exception as ex:
                print(f"  Aguardando build do GitHub Pages ({ex})...")
                await asyncio.sleep(6)
                
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_gh_pages())
