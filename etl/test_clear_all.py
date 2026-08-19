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
        
        result = await page.evaluate('''async () => {
            const wsUrl = `wss://${window.location.host}/app/${window.location.pathname.split('/app/')[1].split('/')[0]}`;
            
            return new Promise((resolve) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
                
                ws.onopen = () => {
                    ws.send(JSON.stringify({
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "OpenDoc",
                        "handle": -1,
                        "params": [window.location.pathname.split('/app/')[1].split('/')[0]]
                    }));
                };
                
                ws.onmessage = (event) => {
                    const msg = JSON.parse(event.data);
                    
                    if (msg.id === 1 && msg.result) {
                        docHandle = msg.result.qReturn.qHandle;
                        // 1. Limpar todas as seleções ativas
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "ClearAll",
                            "handle": docHandle,
                            "params": [false, ""]
                        }));
                    } else if (msg.id === 2) {
                        // 2. Query por Ano-Mes total sem filtros
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "CreateSessionObject",
                            "handle": docHandle,
                            "params": [{
                                "qInfo": { "qType": "test_anomes_totals_cleared" },
                                "qHyperCubeDef": {
                                    "qDimensions": [
                                        { "qDef": { "qFieldDefs": ["Ano-Mes"] } }
                                    ],
                                    "qMeasures": [
                                        { "qDef": { "qDef": "Sum([Valor Líquido] - [Valor Receita Recarga] + ([Valor Receita Recarga] * 4.63)/100)", "qLabel": "Resultado_Liquido" } },
                                        { "qDef": { "qDef": "Min(Dia)", "qLabel": "MinDia" } },
                                        { "qDef": { "qDef": "Max(Dia)", "qLabel": "MaxDia" } }
                                    ],
                                    "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 100, "qWidth": 4 }],
                                    "qSuppressZero": true, "qSuppressMissing": true
                                }
                            }]
                        }));
                    } else if (msg.id === 3 && msg.result) {
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 4,
                            "method": "GetLayout",
                            "handle": msg.result.qReturn.qHandle,
                            "params": []
                        }));
                    } else if (msg.id === 4 && msg.result) {
                        const hc = msg.result.qLayout.qHyperCube;
                        const rows = (hc.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));
                        resolve({ rows });
                        ws.close();
                    }
                };
                
                ws.onerror = () => resolve({ error: 'ws error' });
                setTimeout(() => resolve({ error: 'timeout' }), 15000);
            });
        }''')
        
        print("Totais por Ano-Mes após ClearAll no Qlik Sense:")
        for r in result.get('rows', []):
            print(f"  Ano-Mes: {r[0]} | Resultado Líquido: R$ {r[1]:,.2f} | Dias: {r[2]} até {r[3]}")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
