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
        await page.goto(SHEET_URL, timeout=60000)
        await page.wait_for_timeout(8000)
        
        res = await page.evaluate('''async () => {
            const wsUrl = `wss://${window.location.host}/app/${encodeURIComponent('671fa4f4-eb7d-418f-b4c9-936e87d8011d')}?reloadUri=https://${window.location.host}/`;
            
            return new Promise((resolve) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
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
                        docHandle = openRes.result.qReturn.qHandle;
                        
                        // Test hypercube with Diretor + Grupo + Subgrupo + Linha
                        const c = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_test_hier_dir" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Diretor"] } },
                                    { "qDef": { "qFieldDefs": ["Distrital"] } },
                                    { "qDef": { "qFieldDefs": ["Desc_Grupo"] } },
                                    { "qDef": { "qFieldDefs": ["Desc_Subgrupo"] } },
                                    { "qDef": { "qFieldDefs": ["Desc_Linha"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-08'}, [Dia]={'<=18'}>} [Receita Líquida])", "qLabel": "v26" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-07'}, [Dia]={'<=18'}>} [Receita Líquida])", "qLabel": "v26_06" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2025-08'}, [Dia]={'<=18'}>} [Receita Líquida])", "qLabel": "v25" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 10, "qWidth": 8 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h = c.result.qReturn.qHandle;
                        const l = await send("GetLayout", h, []);
                        const totalRows = l.result.qLayout.qHyperCube.qSize.qcy;
                        
                        // Test hypercube with Diretor + Canal
                        const c_ch = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_test_ch_dir" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Diretor"] } },
                                    { "qDef": { "qFieldDefs": ["Canal"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-08'}, [Dia]={'<=18'}>} [Receita Líquida])", "qLabel": "v26" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 50, "qWidth": 3 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h_ch = c_ch.result.qReturn.qHandle;
                        const l_ch = await send("GetLayout", h_ch, []);
                        const totalRows_ch = l_ch.result.qLayout.qHyperCube.qSize.qcy;
                        
                        resolve({
                            totalRowsHierWithDir: totalRows,
                            totalRowsChWithDir: totalRows_ch,
                            sampleHier: l.result.qLayout.qHyperCube.qDataPages[0]?.qMatrix?.slice(0, 3)
                        });
                        ws.close();
                    } catch (e) {
                        resolve({ error: e.message });
                    }
                };
                
                ws.onmessage = (event) => {
                    const msg = JSON.parse(event.data);
                    if (msg.id && pending[msg.id]) {
                        if (msg.error) pending[msg.id].rej(new Error(msg.error.message));
                        else pending[msg.id].res(msg);
                        delete pending[msg.id];
                    }
                };
            });
        }''')
        
        print("RESULT:", json.dumps(res, indent=2, ensure_ascii=False))
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
