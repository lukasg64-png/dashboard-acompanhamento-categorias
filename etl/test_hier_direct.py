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
            http_credentials={'username': USERNAME, 'password': PASSWORD}
        )
        page = await context.new_page()
        await page.goto(SHEET_URL, timeout=45000)
        await page.wait_for_timeout(6000)
        
        script = """
        () => new Promise((resolve, reject) => {
            const url = `wss://sense.farmaciassaojoao.com.br/app/${encodeURIComponent('671fa4f4-eb7d-418f-b4c9-936e87d8011d')}?reloadUri=https://sense.farmaciassaojoao.com.br/`;
            const ws = new WebSocket(url);
            let docHandle = null;
            let hierObjHandle = null;
            let allRows = [];
            let totalRows = 0;
            let qWidth = 0;
            
            ws.onopen = () => {
                ws.send(JSON.stringify({
                    "jsonrpc": "2.0", "id": 1,
                    "method": "OpenDoc", "handle": -1,
                    "params": ["671fa4f4-eb7d-418f-b4c9-936e87d8011d"]
                }));
            };
            
            ws.onmessage = async (event) => {
                const msg = JSON.parse(event.data);
                
                if (msg.id === 1 && msg.result) {
                    docHandle = msg.result.qReturn.qHandle;
                    
                    // Direct Hierarchy with 9 measures (Group + Subgroup + Line)
                    ws.send(JSON.stringify({
                        "jsonrpc": "2.0", "id": 10,
                        "method": "CreateSessionObject", "handle": docHandle,
                        "params": [{
                            "qInfo": { "qType": "q_hier_9m" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Desc_Grupo"] } },
                                    { "qDef": { "qFieldDefs": ["Desc_Subgrupo"] } },
                                    { "qDef": { "qFieldDefs": ["Desc_Linha"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-08'}>} [Receita Líquida])", "qLabel": "v26" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-07'}>} [Receita Líquida])", "qLabel": "v26_06" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2025-08'}>} [Receita Líquida])", "qLabel": "v25" } },
                                    
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-08'}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL'}>} [Receita Líquida])", "qLabel": "vDig26" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-07'}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL'}>} [Receita Líquida])", "qLabel": "vDig26_06" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2025-08'}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL'}>} [Receita Líquida])", "qLabel": "vDig25" } },
                                    
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-08'}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL','TELE ENTREGA','TELE VENDA'}>} [Receita Líquida])", "qLabel": "vDt26" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-07'}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL','TELE ENTREGA','TELE VENDA'}>} [Receita Líquida])", "qLabel": "vDt26_06" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2025-08'}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL','TELE ENTREGA','TELE VENDA'}>} [Receita Líquida])", "qLabel": "vDt25" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 800, "qWidth": 12 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]
                    }));
                } else if (msg.id === 10 && msg.result) {
                    hierObjHandle = msg.result.qReturn.qHandle;
                    ws.send(JSON.stringify({
                        "jsonrpc": "2.0", "id": 11,
                        "method": "GetLayout", "handle": hierObjHandle, "params": []
                    }));
                } else if (msg.id === 11 && msg.result) {
                    const hc = msg.result.qLayout.qHyperCube;
                    totalRows = hc.qSize.qcy;
                    qWidth = hc.qSize.qcx;
                    const matrix = hc.qDataPages[0]?.qMatrix || [];
                    matrix.forEach(r => allRows.push(r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText)));
                    
                    ws.close();
                    resolve({ totalRows, qWidth, rowsFetched: allRows.length, sample: allRows.slice(0, 5), sumV26: allRows.reduce((s, r) => s + (typeof r[3] === 'number' ? r[3] : 0), 0) });
                }
            };
        })
        """
        res = await page.evaluate(script)
        print("Resultado da Hierarquia Completa:")
        print(json.dumps(res, indent=2, ensure_ascii=False))
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
