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
                    const docHandle = msg.result.qReturn.qHandle;
                    ws.send(JSON.stringify({
                        "jsonrpc": "2.0", "id": 2,
                        "method": "CreateSessionObject", "handle": docHandle,
                        "params": [{
                            "qInfo": { "qType": "q_test_mtd" },
                            "qHyperCubeDef": {
                                "qDimensions": [],
                                "qMeasures": [
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-08'}>} [Receita Líquida])", "qLabel": "Ago_26_D1" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-07'}, [Dia]={'1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19'}>} [Receita Líquida])", "qLabel": "Jul_26_MTD" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2025-08'}, [Dia]={'1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19'}>} [Receita Líquida])", "qLabel": "Ago_25_MTD" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 1, "qWidth": 3 }]
                            }
                        }]
                    }));
                } else if (msg.id === 2 && msg.result) {
                    ws.send(JSON.stringify({
                        "jsonrpc": "2.0", "id": 3,
                        "method": "GetLayout", "handle": msg.result.qReturn.qHandle, "params": []
                    }));
                } else if (msg.id === 3 && msg.result) {
                    const matrix = msg.result.qLayout.qHyperCube.qDataPages[0].qMatrix[0];
                    ws.close();
                    resolve(matrix.map(c => c.qNum));
                }
            };
        })
        """
        res = await page.evaluate(script)
        print("Valores MTD Exatos:")
        print(f"Ago/26 (01 a 19): R$ {res[0]:,.2f}")
        print(f"Jul/26 (01 a 19): R$ {res[1]:,.2f} | MoM: {((res[0]/res[1])-1)*100:+.2f}%")
        print(f"Ago/25 (01 a 19): R$ {res[2]:,.2f} | YoY: {((res[0]/res[2])-1)*100:+.2f}%")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
