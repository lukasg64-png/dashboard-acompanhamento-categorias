import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        errors = []
        page.on('pageerror', lambda err: errors.append(str(err)))
        page.on('console', lambda msg: print('CONSOLE:', msg.type, msg.text))
        
        file_path = r'C:/Users/lucas.alves6/OneDrive - Farmácias São João/Documentos/ANTIGRAVITI/dashboard-acompanhamento-categorias/dist/index.html'
        await page.goto(f'file:///{file_path}')
        await page.wait_for_timeout(5000)
        
        res1 = await page.evaluate('''() => {
            return {
                mesRef: document.getElementById('filterMesRef')?.value,
                kpiCount: document.getElementById('kpiStrip')?.children?.length,
                canaisRows: document.getElementById('tbodyCanais')?.children?.length,
                firstKpiTitle: document.querySelector('.kpi-card-title')?.textContent,
                firstKpiVal: document.querySelector('.kpi-value-main')?.textContent,
                firstKpiSub: document.querySelector('.kpi-sub-value')?.textContent,
                diretoresOptions: Array.from(document.querySelectorAll('#msDiretor .ms-item span')).map(e => e.textContent.trim()),
                distritaisOptionsCount: document.querySelectorAll('#msDistrital .ms-item span')?.length
            };
        }''')
        print('1. AGOSTO INITIAL STATE:', json.dumps(res1, indent=2, ensure_ascii=False))
        
        # Test clicking on a director checkbox
        print('\n2. Clicando no Diretor "Laerti Siqueira"...')
        await page.evaluate('''() => {
            const labels = Array.from(document.querySelectorAll('#msDiretor .ms-item span'));
            const laertiLabel = labels.find(l => l.textContent.includes('Laerti'));
            if (laertiLabel) {
                const cb = laertiLabel.closest('.ms-item').querySelector('input');
                if (cb) cb.click();
            }
        }''')
        await page.wait_for_timeout(1000)
        
        res2 = await page.evaluate('''() => {
            return {
                canaisRows: document.getElementById('tbodyCanais')?.children?.length,
                firstKpiVal: document.querySelector('.kpi-value-main')?.textContent,
                firstKpiSub: document.querySelector('.kpi-sub-value')?.textContent,
                distritaisOptions: Array.from(document.querySelectorAll('#msDistrital .ms-item span')).map(e => e.textContent.trim())
            };
        }''')
        print('AFTER SELECTING LAERTI SIQUEIRA:', json.dumps(res2, indent=2, ensure_ascii=False))
        
        # Test switching to Julho
        print('\n3. Alternando para Julho/26...')
        await page.evaluate('''() => {
            const btnJul = document.querySelector('[data-month="julho"]');
            if (btnJul) btnJul.click();
        }''')
        await page.wait_for_timeout(4000)
        
        res3 = await page.evaluate('''() => {
            return {
                mesRef: document.getElementById('filterMesRef')?.value,
                kpiCount: document.getElementById('kpiStrip')?.children?.length,
                canaisRows: document.getElementById('tbodyCanais')?.children?.length,
                firstKpiTitle: document.querySelector('.kpi-card-title')?.textContent,
                firstKpiVal: document.querySelector('.kpi-value-main')?.textContent,
                firstKpiSub: document.querySelector('.kpi-sub-value')?.textContent
            };
        }''')
        print('JULHO STATE:', json.dumps(res3, indent=2, ensure_ascii=False))
        print('TOTAL ERRORS:', errors)
        
        await page.screenshot(path='test_dashboard_flow.png')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
