import os, sys, asyncio, json, time
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
AGOSTO_DIR = os.path.join(DATA_DIR, 'agosto')

QLIK_URL = "https://sense.farmaciassaojoao.com.br"
APP_ID = "671fa4f4-eb7d-418f-b4c9-936e87d8011d"
SHEET_ID = "ddd70c77-1a06-40d9-aff2-efa4b6b67b24"
SHEET_URL = f"{QLIK_URL}/sense/app/{APP_ID}/sheet/{SHEET_ID}/state/analysis"

USERNAME = "lucas.alves6"
PASSWORD = "Eloise2025*"

async def extract_direct_summaries():
    os.makedirs(AGOSTO_DIR, exist_ok=True)
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  EXTRAÇÃO DIRETA DOS MODELOS DE DADOS DO QLIK SENSE (AGOSTO D-1)")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={'username': USERNAME, 'password': PASSWORD},
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print("  1/2 Conectando ao Qlik Sense...")
        await page.goto(SHEET_URL, timeout=60000)
        await page.wait_for_timeout(8000)
        
        print("  2/2 Executando consultas agregadas no Qlik Engine...")
        queries_script = '''async () => {
            const wsUrl = `wss://${window.location.host}/app/${window.location.pathname.split('/app/')[1].split('/')[0]}`;
            
            return new Promise((resolve) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
                const results = {};
                
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
                        
                        // Query 1: Canais x Dia
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "CreateSessionObject",
                            "handle": docHandle,
                            "params": [{
                                "qInfo": { "qType": "canais_dia" },
                                "qHyperCubeDef": {
                                    "qDimensions": [
                                        { "qDef": { "qFieldDefs": ["Canal"] } },
                                        { "qDef": { "qFieldDefs": ["Ano-Mes"] } },
                                        { "qDef": { "qFieldDefs": ["Dia"] } }
                                    ],
                                    "qMeasures": [
                                        { "qDef": { "qDef": "Sum([Valor Líquido])", "qLabel": "Venda" } }
                                    ],
                                    "qInitialDataFetch": [{
                                        "qTop": 0,
                                        "qLeft": 0,
                                        "qHeight": 1000,
                                        "qWidth": 4
                                    }],
                                    "qSuppressZero": true,
                                    "qSuppressMissing": true
                                }
                            }]
                        }));
                    } else if (msg.id === 2 && msg.result) {
                        const layout = msg.result;
                        
                        // Obter layout da query 1
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "GetLayout",
                            "handle": msg.result.qReturn.qHandle,
                            "params": []
                        }));
                    } else if (msg.id === 3 && msg.result) {
                        const hc = msg.result.qLayout.qHyperCube;
                        results.canais_dia = (hc.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));
                        
                        ws.close();
                        resolve(results);
                    }
                };
                
                ws.onerror = (e) => resolve({ error: 'ws error' });
                setTimeout(() => resolve({ error: 'timeout' }), 20000);
            });
        }'''
        
        res = await page.evaluate(queries_script)
        await browser.close()
        
        print(f"  ✅ Extração concluída em {time.time() - t0:.2f}s!")
        canais_data = res.get('canais_dia', [])
        print(f"  Total de linhas Canal x Dia: {len(canais_data)}")
        if canais_data:
            print("  Exemplo de linha:", canais_data[0])

if __name__ == '__main__':
    asyncio.run(extract_direct_summaries())
