import os, sys, asyncio, json
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = f"file:///{os.path.join(BASE_DIR, 'dist', 'index.html').replace(os.sep, '/')}"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        print("1. Abrindo dist/index.html em Agosto...")
        await page.goto(INDEX_PATH)
        await page.wait_for_timeout(2000)
        
        kpi_ago = await page.locator('#kpiStrip .kpi-value').first.inner_text()
        ref_ago = await page.locator('#refPeriodo').inner_text()
        print(f"   KPI Agosto: {kpi_ago} | Período: {ref_ago}")
        
        print("2. Trocando para Julho/2026...")
        await page.locator('#filterMesReferencia').select_option('julho')
        await page.wait_for_timeout(2000)
        
        kpi_jul = await page.locator('#kpiStrip .kpi-value').first.inner_text()
        ref_jul = await page.locator('#refPeriodo').inner_text()
        print(f"   KPI Julho: {kpi_jul} | Período: {ref_jul}")
        
        print("3. Retornando para Agosto/2026...")
        await page.locator('#filterMesReferencia').select_option('agosto')
        await page.wait_for_timeout(2000)
        
        kpi_ago_2 = await page.locator('#kpiStrip .kpi-value').first.inner_text()
        ref_ago_2 = await page.locator('#refPeriodo').inner_text()
        print(f"   KPI Agosto (retorno): {kpi_ago_2} | Período: {ref_ago_2}")
        
        assert kpi_ago == 'R$ 519,9 Mi', f"Esperado R$ 519,9 Mi, obtido {kpi_ago}"
        assert '882' in kpi_jul or '88' in kpi_jul, f"Esperado faturamento de Julho ~882 Mi, obtido {kpi_jul}"
        assert kpi_ago_2 == 'R$ 519,9 Mi', f"Esperado R$ 519,9 Mi no retorno, obtido {kpi_ago_2}"
        
        print("\n✅ TESTE DE TROCA DE MÊS 100% APROVADO!")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
