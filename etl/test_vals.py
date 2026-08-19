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
                        // Query usando Sum(Receita Líquida) e Sum(Valor Líquido)
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "CreateSessionObject",
                            "handle": docHandle,
                            "params": [{
                                "qInfo": { "qType": "test_vals" },
                                "qHyperCubeDef": {
                                    "qDimensions": [
                                        { "qDef": { "qFieldDefs": ["Canal"] } },
                                        { "qDef": { "qFieldDefs": ["Ano-Mes"] } }
                                    ],
                                    "qMeasures": [
                                        { "qDef": { "qDef": "Sum([Valor Líquido])", "qLabel": "Valor_Liquido" } },
                                        { "qDef": { "qDef": "Sum([Receita Líquida])", "qLabel": "Receita_Liquida" } }
                                    ],
                                    "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 100, "qWidth": 4 }],
                                    "qSuppressZero": true, "qSuppressMissing": true
                                }
                            }]
                        }));
                    } else if (msg.id === 2 && msg.result) {
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "GetLayout",
                            "handle": msg.result.qReturn.qHandle,
                            "params": []
                        }));
                    } else if (msg.id === 3 && msg.result) {
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
        
        print("Valores de Venda por Canal e Ano-Mes no Qlik Sense:")
        for r in result.get('rows', []):
            print(f"  {r[0]:<25} | {r[1]} | V_Liq: R$ {r[2]:,.2f} | Rec_Liq: R$ {r[3]:,.2f}")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
