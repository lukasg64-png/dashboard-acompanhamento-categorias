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
        
        # Testar listar todos os objetos do App via Engine API WebSocket
        res = await page.evaluate('''async () => {
            const wsUrl = `wss://${window.location.host}/app/${window.location.pathname.split('/app/')[1].split('/')[0]}`;
            
            return new Promise((resolve) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
                const objects = [];
                
                ws.onopen = () => {
                    // 1. OpenDoc
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
                        // 2. GetObjects (sheets, tables, master items)
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "GetAllInfos",
                            "handle": docHandle,
                            "params": []
                        }));
                    } else if (msg.id === 2 && msg.result) {
                        const infos = msg.result.qInfos;
                        resolve({ docHandle, count: infos.length, infos: infos.slice(0, 50) });
                        ws.close();
                    }
                };
                
                ws.onerror = (e) => resolve({ error: 'ws error' });
                setTimeout(() => resolve({ error: 'timeout' }), 10000);
            });
        }''')
        
        print("Resultado da listagem de objetos Qlik:")
        print(json.dumps(res, indent=2))

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
