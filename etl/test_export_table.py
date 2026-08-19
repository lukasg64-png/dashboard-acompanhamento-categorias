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
        
        # Testar ExportData no objeto ZKJqXsu
        res = await page.evaluate('''async () => {
            const wsUrl = `wss://${window.location.host}/app/${window.location.pathname.split('/app/')[1].split('/')[0]}`;
            
            return new Promise((resolve) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
                let objHandle = null;
                
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
                        // Obter objeto da tabela dinamica ZKJqXsu
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "GetObject",
                            "handle": docHandle,
                            "params": ["ZKJqXsu"]
                        }));
                    } else if (msg.id === 2 && msg.result) {
                        objHandle = msg.result.qReturn.qHandle;
                        // Chamar ExportData
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "ExportData",
                            "handle": objHandle,
                            "params": {
                                "qFileType": "OOXML",
                                "qPath": "",
                                "qFileName": "export_categorias.xlsx",
                                "qExportState": "A"
                            }
                        }));
                    } else if (msg.id === 3) {
                        resolve(msg);
                        ws.close();
                    }
                };
                
                ws.onerror = (e) => resolve({ error: 'ws error' });
                setTimeout(() => resolve({ error: 'timeout' }), 45000);
            });
        }''')
        
        print("Resultado do ExportData:")
        print(json.dumps(res, indent=2))
        
        if res.get('result') and res['result'].get('qUrl'):
            download_url = QLIK_URL + res['result']['qUrl']
            print(f"Baixando arquivo exportado de {download_url}...")
            
            # Baixar pelo browser
            download_page = await context.new_page()
            async with download_page.expect_download() as download_info:
                await download_page.goto(download_url)
            download = await download_info.value
            save_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'qlik_export_agosto.xlsx')
            await download.save_as(save_path)
            print(f"✅ Arquivo salvo em {save_path} ({os.path.getsize(save_path)} bytes)!")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
