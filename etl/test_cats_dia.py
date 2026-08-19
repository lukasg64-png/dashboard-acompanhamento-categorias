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
        try:
            await page.wait_for_selector('.qv-panel-sheet', timeout=30000)
        except:
            await page.wait_for_timeout(10000)
            
        script = """
        () => new Promise((resolve, reject) => {
            const url = `wss://sense.farmaciassaojoao.com.br/app/${encodeURIComponent('671fa4f4-eb7d-418f-b4c9-936e87d8011d')}?reloadUri=https://sense.farmaciassaojoao.com.br/`;
            const ws = new WebSocket(url);
            let msgId = 1;
            const pending = {};
            
            function send(method, handle, params) {
                return new Promise((res, rej) => {
                    const id = msgId++;
                    pending[id] = { res, rej };
                    ws.send(JSON.stringify({ "jsonrpc": "2.0", "id": id, "method": method, "handle": handle, "params": params }));
                });
            }
            
            ws.onopen = async () => {
                try {
                    const openRes = await send("OpenDoc", -1, ["671fa4f4-eb7d-418f-b4c9-936e87d8011d"]);
                    const docHandle = openRes.result.qReturn.qHandle;
                    
                    // Categorias x Dia (3 dimensões: Grupo, Subgrupo, Dia) + 9 medidas
                    const c = await send("CreateSessionObject", docHandle, [{
                        "qInfo": { "qType": "q_cats_dia_3p" },
                        "qHyperCubeDef": {
                            "qDimensions": [
                                { "qDef": { "qFieldDefs": ["Desc_Grupo"] } },
                                { "qDef": { "qFieldDefs": ["Desc_Subgrupo"] } },
                                { "qDef": { "qFieldDefs": ["Dia"] } }
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
                    }]);
                    const h = c.result.qReturn.qHandle;
                    const l = await send("GetLayout", h, []);
                    const totalRows = l.result.qLayout.qHyperCube.qSize.qcy;
                    const qWidth = l.result.qLayout.qHyperCube.qSize.qcx;
                    
                    let rows = [];
                    let top = 0;
                    while (top < totalRows) {
                        const height = Math.min(800, totalRows - top);
                        const pageRes = await send("GetHyperCubeData", h, ["/qHyperCubeDef", [{ "qTop": top, "qLeft": 0, "qHeight": height, "qWidth": qWidth }]]);
                        const matrix = pageRes.result.qDataPages[0]?.qMatrix || [];
                        if (matrix.length === 0) break;
                        matrix.forEach(r => rows.push(r.map(cell => cell.qNum !== 'NaN' && typeof cell.qNum === 'number' ? cell.qNum : cell.qText)));
                        top += matrix.length;
                    }
                    ws.close();
                    resolve({ totalRows, rowsCount: rows.length, sample: rows.slice(0, 3) });
                } catch (e) {
                    ws.close();
                    reject(e);
                }
            };
            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.id && pending[msg.id]) {
                    const { res, rej } = pending[msg.id];
                    delete pending[msg.id];
                    if (msg.error) rej(msg.error);
                    else res(msg);
                }
            };
        })
        """
        res = await page.evaluate(script)
        print("Resultado Categorias x Dia:")
        print(json.dumps(res, indent=2, ensure_ascii=False))
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
