import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        file_path = r'C:/Users/lucas.alves6/OneDrive - Farmácias São João/Documentos/ANTIGRAVITI/dashboard-acompanhamento-categorias/dist/index.html'
        await page.goto(f'file:///{file_path}')
        await page.wait_for_timeout(4000)
        
        # 1. Open Diretor dropdown
        print('1. Abrindo dropdown de Diretor...')
        btn_dir = page.locator('#msDiretor .ms-btn')
        await btn_dir.click()
        await page.wait_for_timeout(500)
        
        # 2. Click "Laerti Siqueira"
        print('2. Selecionando "Laerti Siqueira"...')
        cb_laerti = page.locator('#msDiretor input[value="Laerti Siqueira"]')
        await cb_laerti.click()
        await page.wait_for_timeout(1000)
        
        res = await page.evaluate('''() => {
            return {
                kpi1_title: document.querySelectorAll('.kpi-card-title')[0]?.textContent,
                kpi1_val: document.querySelectorAll('.kpi-value-main')[0]?.textContent,
                kpi1_sub: document.querySelectorAll('.kpi-sub-value')[0]?.textContent,
                kpi2_title: document.querySelectorAll('.kpi-card-title')[1]?.textContent,
                kpi2_val: document.querySelectorAll('.kpi-value-main')[1]?.textContent,
                distritais_disponiveis: Array.from(document.querySelectorAll('#msDistrital .ms-item span')).map(e => e.textContent.trim()),
                canais_rows: document.querySelectorAll('#tbodyCanais tr')?.length,
                categorias_rows: document.querySelectorAll('#tbodyCategorias tr')?.length
            };
        }''')
        print('RESULT FOR LAERTI SIQUEIRA:', json.dumps(res, indent=2, ensure_ascii=False))
        
        # 3. Click "Cintia Silva" instead
        print('\n3. Trocando para "Cintia Silva"...')
        await cb_laerti.click() # uncheck
        cb_cintia = page.locator('#msDiretor input[value="Cintia Silva"]')
        await cb_cintia.click() # check
        await page.wait_for_timeout(1000)
        
        res_cintia = await page.evaluate('''() => {
            return {
                kpi1_val: document.querySelectorAll('.kpi-value-main')[0]?.textContent,
                kpi1_sub: document.querySelectorAll('.kpi-sub-value')[0]?.textContent,
                distritais_disponiveis: Array.from(document.querySelectorAll('#msDistrital .ms-item span')).map(e => e.textContent.trim()),
                canais_rows: document.querySelectorAll('#tbodyCanais tr')?.length
            };
        }''')
        print('RESULT FOR CINTIA SILVA:', json.dumps(res_cintia, indent=2, ensure_ascii=False))
        
        # 4. Uncheck all to return to total
        print('\n4. Desmarcando tudo para voltar ao total da rede...')
        await cb_cintia.click()
        await page.wait_for_timeout(1000)
        
        res_total = await page.evaluate('''() => {
            return {
                kpi1_val: document.querySelectorAll('.kpi-value-main')[0]?.textContent,
                kpi1_sub: document.querySelectorAll('.kpi-sub-value')[0]?.textContent,
                distritais_count: document.querySelectorAll('#msDistrital .ms-item')?.length
            };
        }''')
        print('RESULT TOTAL REDE:', json.dumps(res_total, indent=2, ensure_ascii=False))
        
        await page.screenshot(path='test_director_filter.png')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
