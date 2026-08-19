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
        browser = await p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={'username': USERNAME, 'password': PASSWORD},
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print("1. Conectando ao Qlik Sense...")
        await page.goto(SHEET_URL, timeout=60000)
        await page.wait_for_timeout(8000)
        
        print("2. Criando Session HyperCube agregado de Agosto (D-1)...")
        t0 = time.time()
        result = await page.evaluate('''async () => {
            const wsUrl = `wss://${window.location.host}/app/${window.location.pathname.split('/app/')[1].split('/')[0]}`;
            
            return new Promise((resolve) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
                let sessionHandle = null;
                
                ws.onopen = () => {
                    ws.send(JSON.stringify({
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "OpenDoc",
                        "handle": -1,
                        "params": [window.location.pathname.split('/app/')[1].split('/')[0]]
                    }));
                };
                
                ws.onmessage = async (event) => {
                    const msg = JSON.parse(event.data);
                    
                    if (msg.id === 1 && msg.result) {
                        docHandle = msg.result.qReturn.qHandle;
                        
                        // 1. Criar Session Object com HyperCube agregado para Agosto
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "CreateSessionObject",
                            "handle": docHandle,
                            "params": [{
                                "qInfo": { "qType": "agosto_summary" },
                                "qHyperCubeDef": {
                                    "qDimensions": [
                                        { "qDef": { "qFieldDefs": ["Canal"] } },
                                        { "qDef": { "qFieldDefs": ["Desc_Grupo"] } },
                                        { "qDef": { "qFieldDefs": ["Desc_Subgrupo"] } },
                                        { "qDef": { "qFieldDefs": ["Agrupamento"] } },
                                        { "qDef": { "qFieldDefs": ["Desc_Linha"] } },
                                        { "qDef": { "qFieldDefs": ["Laboratorio"] } },
                                        { "qDef": { "qFieldDefs": ["Dia"] } }
                                    ],
                                    "qMeasures": [
                                        { "qDef": { "qDef": "Sum({<[Ano-Mes]={'2025-08'}>} [Valor Líquido])", "qLabel": "Venda_Valor" } },
                                        { "qDef": { "qDef": "Sum({<[Ano-Mes]={'2025-08'}>} [Quantidade Saldo])", "qLabel": "Quantidade" } },
                                        { "qDef": { "qDef": "Count({<[Ano-Mes]={'2025-08'}>} DISTINCT [Cliente_ID])", "qLabel": "Clientes" } }
                                    ],
                                    "qInitialDataFetch": [{
                                        "qTop": 0,
                                        "qLeft": 0,
                                        "qHeight": 50,
                                        "qWidth": 10
                                    }],
                                    "qSuppressZero": true,
                                    "qSuppressMissing": true
                                }
                            }]
                        }));
                    } else if (msg.id === 2 && msg.result) {
                        sessionHandle = msg.result.qReturn.qHandle;
                        
                        // Obter layout
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "GetLayout",
                            "handle": sessionHandle,
                            "params": []
                        }));
                    } else if (msg.id === 3 && msg.result) {
                        const layout = msg.result.qLayout;
                        const hc = layout.qHyperCube;
                        const rows = (hc.qDataPages[0]?.qMatrix || []).map(row => row.map(c => c.qText));
                        
                        resolve({
                            size: hc.qSize,
                            sampleRows: rows.slice(0, 10),
                            headers: [
                                ...hc.qDimensionInfo.map(d => d.qFallbackTitle),
                                ...hc.qMeasureInfo.map(m => m.qFallbackTitle)
                            ]
                        });
                        ws.close();
                    }
                };
                
                ws.onerror = (e) => resolve({ error: 'ws error' });
                setTimeout(() => resolve({ error: 'timeout' }), 20000);
            });
        }''')
        
        print(f"✅ Consulta executada em {time.time() - t0:.2f}s!")
        print("Resultado do Session HyperCube de Agosto:")
        print(json.dumps(result, indent=2))

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
