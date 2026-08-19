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
        
        print("1. Conectando ao Qlik Sense...")
        await page.goto(SHEET_URL, timeout=60000)
        await page.wait_for_timeout(10000)
        
        # Inspecionar objetos dentro da pasta ddd70c77-1a06-40d9-aff2-efa4b6b67b24
        res = await page.evaluate('''async () => {
            const wsUrl = `wss://${window.location.host}/app/${window.location.pathname.split('/app/')[1].split('/')[0]}`;
            
            return new Promise((resolve) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
                let sheetHandle = null;
                
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
                        // Obter objeto da pasta
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "GetObject",
                            "handle": docHandle,
                            "params": ["ddd70c77-1a06-40d9-aff2-efa4b6b67b24"]
                        }));
                    } else if (msg.id === 2 && msg.result) {
                        sheetHandle = msg.result.qReturn.qHandle;
                        // GetLayout da pasta
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "GetLayout",
                            "handle": sheetHandle,
                            "params": []
                        }));
                    } else if (msg.id === 3 && msg.result) {
                        const layout = msg.result.qLayout;
                        const cells = layout.cells || [];
                        resolve({ title: layout.qMeta?.title, cellCount: cells.length, cells });
                        ws.close();
                    }
                };
                
                ws.onerror = (e) => resolve({ error: 'ws error' });
                setTimeout(() => resolve({ error: 'timeout' }), 10000);
            });
        }''')
        
        print("Objetos da pasta ddd70c77-1a06-40d9-aff2-efa4b6b67b24:")
        print(json.dumps(res, indent=2))

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
