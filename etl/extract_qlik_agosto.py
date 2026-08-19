"""
extract_qlik_agosto.py — Extração Automática de Agosto (D-1) via Qlik Sense Engine API
Conecta ao Qlik Sense Enterprise, cria Session HyperCube agregado por Hierarquia x Canal x Dia
para o mês de Agosto e salva a base atualizada em data/agosto/qlik_agosto_daily.parquet e data/agosto/*.json
"""
import os, sys, time, json, asyncio
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
AGOSTO_DIR = os.path.join(DATA_DIR, 'agosto')
PARQUET_OUT = os.path.join(AGOSTO_DIR, 'qlik_agosto_daily.parquet')

QLIK_URL = "https://sense.farmaciassaojoao.com.br"
APP_ID = "671fa4f4-eb7d-418f-b4c9-936e87d8011d"
SHEET_ID = "ddd70c77-1a06-40d9-aff2-efa4b6b67b24"
SHEET_URL = f"{QLIK_URL}/sense/app/{APP_ID}/sheet/{SHEET_ID}/state/analysis"

USERNAME = "lucas.alves6"
PASSWORD = "Eloise2025*"

async def extract_qlik_agosto_data():
    os.makedirs(AGOSTO_DIR, exist_ok=True)
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  EXTRAINDO DADOS DE AGOSTO (D-1) DO QLIK SENSE ENTERPRISE")
    print("=" * 70)

    async with async_playwright() as p:
        print("  1/3 Conectando e autenticando no Qlik Sense...")
        browser = await p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={'username': USERNAME, 'password': PASSWORD},
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        await page.goto(SHEET_URL, timeout=60000)
        await page.wait_for_timeout(8000)
        print(f"  ✅ Conectado ao Qlik Sense: {await page.title()}")

        print("  2/3 Consultando Engine API para extração agregada por Dia...")
        # Executar extração paginada de HyperCube
        extract_script = '''async () => {
            const wsUrl = `wss://${window.location.host}/app/${window.location.pathname.split('/app/')[1].split('/')[0]}`;
            
            return new Promise((resolve) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
                let sessionHandle = null;
                const allRows = [];
                let headers = [];
                
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
                        
                        // Criar Session Object agregado por Canal, Hierarquia e Dia
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "CreateSessionObject",
                            "handle": docHandle,
                            "params": [{
                                "qInfo": { "qType": "agosto_daily_extract" },
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
                                    "qSuppressZero": true,
                                    "qSuppressMissing": true
                                }
                            }]
                        }));
                    } else if (msg.id === 2 && msg.result) {
                        sessionHandle = msg.result.qReturn.qHandle;
                        
                        // Obter layout e dimensões do HyperCube
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
                        const totalRows = hc.qSize.qcy;
                        const colsCount = hc.qSize.qcx;
                        headers = [
                            ...hc.qDimensionInfo.map(d => d.qFallbackTitle),
                            ...hc.qMeasureInfo.map(m => m.qFallbackTitle)
                        ];
                        
                        // Buscar lotes de dados
                        const PAGE_SIZE = 1000;
                        let currentTop = 0;
                        
                        async function fetchNextPage() {
                            if (currentTop >= totalRows || currentTop >= 50000) { // Limite de linhas
                                ws.close();
                                resolve({ headers, rows: allRows, totalRows });
                                return;
                            }
                            
                            const reqId = 100 + currentTop;
                            ws.send(JSON.stringify({
                                "jsonrpc": "2.0",
                                "id": reqId,
                                "method": "GetHyperCubeData",
                                "handle": sessionHandle,
                                "params": ["/qHyperCubeDef", [{
                                    "qTop": currentTop,
                                    "qLeft": 0,
                                    "qHeight": Math.min(PAGE_SIZE, totalRows - currentTop),
                                    "qWidth": colsCount
                                }]]
                            }));
                        }
                        
                        // Iniciar paginação
                        fetchNextPage();
                        
                    } else if (msg.id >= 100 && msg.result) {
                        const qMatrix = msg.result.qDataPages[0]?.qMatrix || [];
                        for (const r of qMatrix) {
                            allRows.push(r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));
                        }
                        currentTop = allRows.length;
                        fetchNextPage();
                    }
                };
                
                ws.onerror = (e) => resolve({ error: 'ws error' });
                setTimeout(() => resolve({ headers, rows: allRows, totalRows: allRows.length, timeout: true }), 45000);
            });
        }'''
        
        data_res = await page.evaluate(extract_script)
        await browser.close()
        
        headers = data_res.get('headers', [])
        rows = data_res.get('rows', [])
        print(f"  ✅ Extração finalizada em {time.time() - t0:.2f}s! Total de {len(rows)} registros obtidos.")
        
        if not rows:
            print("  ⚠️ Nenhuma linha retornada. Mantendo base anterior.")
            return

        # Converter para DataFrame
        df = pd.DataFrame(rows, columns=headers)
        print("  Colunas obtidas:", list(df.columns))
        print("  Primeiras linhas:\n", df.head(3))
        
        # Salvar Parquet de Agosto
        df.to_parquet(PARQUET_OUT, index=False)
        print(f"  💾 Base de Agosto salva em {PARQUET_OUT} ({os.path.getsize(PARQUET_OUT)/1024:.1f} KB)")
        
        return df

def main():
    asyncio.run(extract_qlik_agosto_data())

if __name__ == '__main__':
    main()
