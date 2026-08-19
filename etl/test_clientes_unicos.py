import os, sys, asyncio, json, time
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
        print("1. Conectando ao Qlik Sense...")
        browser = await p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={'username': USERNAME, 'password': PASSWORD},
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        await page.goto(SHEET_URL, timeout=60000)
        try:
            await page.wait_for_selector('.qv-panel-sheet', timeout=45000)
        except Exception:
            await page.wait_for_timeout(10000)
        await page.wait_for_timeout(3000)
        
        print("2. Testando cálculo de Clientes Únicos e Cupons por Canal e Categoria...")
        t0 = time.time()
        result = await page.evaluate('''async () => {
            const wsUrl = `wss://${window.location.host}/app/${encodeURIComponent('671fa4f4-eb7d-418f-b4c9-936e87d8011d')}?reloadUri=https://${window.location.host}/`;
            
            return new Promise((resolve) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
                const results = {};
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
                        
                        const maxDia = 18;
                        const dayFilter = `[Dia]={"<=${maxDia}"}`;
                        
                        // 1. Clientes únicos por Canal (Ago/26, Jul/26, Ago/25)
                        const c1 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_clientes_canal" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Canal"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": `Count({1<[Ano-Mes]={'2026-08'}, ${dayFilter}>} distinct [Cliente_ID])`, "qLabel": "cli_ago26" } },
                                    { "qDef": { "qDef": `Count({1<[Ano-Mes]={'2026-07'}, ${dayFilter}>} distinct [Cliente_ID])`, "qLabel": "cli_jul26" } },
                                    { "qDef": { "qDef": `Count({1<[Ano-Mes]={'2025-08'}, ${dayFilter}>} distinct [Cliente_ID])`, "qLabel": "cli_ago25" } },
                                    { "qDef": { "qDef": `Count({1<[Ano-Mes]={'2026-08'}, ${dayFilter}>} distinct [Nr_Cupons])`, "qLabel": "cup_ago26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-08'}, ${dayFilter}>} [Receita Líquida])`, "qLabel": "venda_ago26" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 100, "qWidth": 6 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h1 = c1.result.qReturn.qHandle;
                        const l1 = await send("GetLayout", h1, []);
                        results.canais = (l1.result.qLayout.qHyperCube.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));
                        
                        // 2. Clientes únicos por Grupo de Categoria (Ago/26, Jul/26, Ago/25)
                        const c2 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_clientes_grupo" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Desc_Grupo"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": `Count({1<[Ano-Mes]={'2026-08'}, ${dayFilter}>} distinct [Cliente_ID])`, "qLabel": "cli_ago26" } },
                                    { "qDef": { "qDef": `Count({1<[Ano-Mes]={'2026-07'}, ${dayFilter}>} distinct [Cliente_ID])`, "qLabel": "cli_jul26" } },
                                    { "qDef": { "qDef": `Count({1<[Ano-Mes]={'2025-08'}, ${dayFilter}>} distinct [Cliente_ID])`, "qLabel": "cli_ago25" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-08'}, ${dayFilter}>} [Receita Líquida])`, "qLabel": "venda_ago26" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 100, "qWidth": 5 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h2 = c2.result.qReturn.qHandle;
                        const l2 = await send("GetLayout", h2, []);
                        results.grupos = (l2.result.qLayout.qHyperCube.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));

                        // 3. Total Geral Empresa de Clientes Únicos (Distinct na base inteira)
                        const c3 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_clientes_totais" },
                            "qHyperCubeDef": {
                                "qMeasures": [
                                    { "qDef": { "qDef": `Count({1<[Ano-Mes]={'2026-08'}, ${dayFilter}>} distinct [Cliente_ID])`, "qLabel": "total_cli_ago26" } },
                                    { "qDef": { "qDef": `Count({1<[Ano-Mes]={'2026-07'}, ${dayFilter}>} distinct [Cliente_ID])`, "qLabel": "total_cli_jul26" } },
                                    { "qDef": { "qDef": `Count({1<[Ano-Mes]={'2025-08'}, ${dayFilter}>} distinct [Cliente_ID])`, "qLabel": "total_cli_ago25" } },
                                    { "qDef": { "qDef": `Count({1<[Ano-Mes]={'2026-08'}, ${dayFilter}>} distinct [Nr_Cupons])`, "qLabel": "total_cup_ago26" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 1, "qWidth": 4 }]
                            }
                        }]);
                        const h3 = c3.result.qReturn.qHandle;
                        const l3 = await send("GetLayout", h3, []);
                        results.totais = (l3.result.qLayout.qHyperCube.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));

                        resolve(results);
                        ws.close();
                    } catch (err) {
                        resolve({ error: err.message });
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
                
                ws.onerror = (e) => resolve({ error: 'ws error' });
                setTimeout(() => resolve({ error: 'timeout' }), 45000);
            });
        }''')
        
        elapsed = time.time() - t0
        print(f"✅ Consulta finalizada em {elapsed:.2f}s!")
        print("\n📊 TOTAIS DE CLIENTES ÚNICOS:")
        print(json.dumps(result.get('totais'), indent=2))
        
        print("\n🛍️ CLIENTES ÚNICOS POR CANAL:")
        for r in result.get('canais', []):
            print(f"  {r[0]:<25} | Ago/26: {r[1]:>10} | Jul/26: {r[2]:>10} | Ago/25: {r[3]:>10} | Cupons: {r[4]:>10} | Venda: R$ {r[5]:>12,.2f}")
            
        print("\n📦 CLIENTES ÚNICOS POR GRUPO DE CATEGORIA:")
        for r in result.get('grupos', []):
            print(f"  {r[0]:<25} | Ago/26: {r[1]:>10} | Jul/26: {r[2]:>10} | Ago/25: {r[3]:>10} | Venda: R$ {r[4]:>12,.2f}")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
