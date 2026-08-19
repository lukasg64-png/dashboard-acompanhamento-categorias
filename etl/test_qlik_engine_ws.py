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
        
        # Testar engine WebSocket ou objetos globais
        res = await page.evaluate('''async () => {
            const results = {};
            results.hasQlik = typeof window.qlik !== 'undefined';
            results.hasRequire = typeof window.require !== 'undefined';
            results.title = document.title;
            results.url = window.location.href;
            
            // Obter todos os elementos com texto ou títulos
            const elements = Array.from(document.querySelectorAll('h1, h2, h3, h4, .title, [tid], .qv-object'));
            results.headings = elements.map(e => e.innerText.trim()).filter(Boolean);
            
            // Testar conexão WebSocket direta com Qlik Engine
            const wsUrl = `wss://${window.location.host}/app/${window.location.pathname.split('/app/')[1].split('/')[0]}`;
            results.wsUrl = wsUrl;
            
            return new Promise((resolve) => {
                try {
                    const ws = new WebSocket(wsUrl);
                    ws.onopen = () => {
                        results.wsOpen = true;
                        // Enviar OpenDoc
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "OpenDoc",
                            "handle": -1,
                            "params": [window.location.pathname.split('/app/')[1].split('/')[0]]
                        }));
                    };
                    ws.onmessage = (event) => {
                        results.wsMessage = JSON.parse(event.data);
                        ws.close();
                        resolve(results);
                    };
                    ws.onerror = (err) => {
                        results.wsError = true;
                        resolve(results);
                    };
                    setTimeout(() => resolve(results), 5000);
                } catch(e) {
                    results.catchError = e.message;
                    resolve(results);
                }
            });
        }''')
        
        print("Resultado da avaliação:")
        print(json.dumps(res, indent=2))

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
