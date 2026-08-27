"""
extract_qlik_setembro.py — Extrai dados de venda D-1 do Qlik Sense para Setembro/2026.
Query simplificada: apenas Desc_Linha × Dia (sem canais, sem grupo/subgrupo).
Gera JSON com realizado por linha × dia para comparar com as metas.
"""
import os, sys, time, json, asyncio
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'setembro')

QLIK_URL = "https://sense.farmaciassaojoao.com.br"
APP_ID = "671fa4f4-eb7d-418f-b4c9-936e87d8011d"
SHEET_ID = "ddd70c77-1a06-40d9-aff2-efa4b6b67b24"
SHEET_URL = f"{QLIK_URL}/sense/app/{APP_ID}/sheet/{SHEET_ID}/state/analysis"

USERNAME = "lucas.alves6"
PASSWORD = "Eloise2025*"

async def fetch_qlik_setembro():
    """Conecta ao Qlik Sense e extrai Desc_Linha × Dia para Set/2026."""
    os.makedirs(DATA_DIR, exist_ok=True)
    t0 = time.time()
    print("\n" + "=" * 60)
    print("  EXTRAINDO DADOS D-1 DO QLIK SENSE — SETEMBRO/2026")
    print("=" * 60)

    async with async_playwright() as p:
        print("  1/3 Conectando ao Qlik Sense...")
        browser = await p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        context = await browser.new_context(
            ignore_https_errors=True,
            http_credentials={'username': USERNAME, 'password': PASSWORD},
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        await page.goto(SHEET_URL, timeout=60000)
        await page.wait_for_timeout(8000)

        print("  2/3 Executando query Desc_Linha × Dia (Set/2026)...")

        # Query: Desc_Linha × Dia com filtro Set/2026 (Ano-Mes = '2026-09')
        # Usa HyperCube com set analysis para filtrar apenas setembro
        query_js = '''async () => {
            const appId = window.location.pathname.split('/app/')[1].split('/')[0];
            const wsUrl = `wss://${window.location.host}/app/${appId}`;
            
            return new Promise((resolve) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
                let allRows = [];
                let objHandle = null;
                
                ws.onopen = () => {
                    ws.send(JSON.stringify({
                        "jsonrpc": "2.0", "id": 1, "method": "OpenDoc",
                        "handle": -1, "params": [appId]
                    }));
                };
                
                ws.onmessage = (event) => {
                    const msg = JSON.parse(event.data);
                    
                    if (msg.id === 1 && msg.result) {
                        docHandle = msg.result.qReturn.qHandle;
                        
                        // Criar HyperCube: Desc_Linha × Dia com Set Analysis para Set/2026
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0", "id": 10,
                            "method": "CreateSessionObject",
                            "handle": docHandle,
                            "params": [{
                                "qInfo": { "qType": "q_set_linha_dia" },
                                "qHyperCubeDef": {
                                    "qDimensions": [
                                        { "qDef": { "qFieldDefs": ["Desc_Linha"] } },
                                        { "qDef": { "qFieldDefs": ["Dia"] } }
                                    ],
                                    "qMeasures": [{
                                        "qDef": {
                                            "qDef": "Sum({<[Ano-Mes]={'2026-09'}>} [Resultado Liquido])",
                                            "qLabel": "Venda Set26"
                                        }
                                    }],
                                    "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 0, "qWidth": 3 }],
                                    "qSuppressZero": true,
                                    "qSuppressMissing": true
                                }
                            }]
                        }));
                    } else if (msg.id === 10 && msg.result) {
                        objHandle = msg.result.qReturn.qHandle;
                        // Obter layout para saber o tamanho total
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0", "id": 11,
                            "method": "GetLayout", "handle": objHandle, "params": []
                        }));
                    } else if (msg.id === 11 && msg.result) {
                        const hc = msg.result.qLayout.qHyperCube;
                        const totalRows = hc.qSize.qcy;
                        const totalCols = hc.qSize.qcx;
                        console.log(`Total rows: ${totalRows}`);
                        
                        if (totalRows === 0) {
                            ws.close();
                            resolve({ rows: [], totalRows: 0, status: 'empty' });
                            return;
                        }
                        
                        // Paginar em blocos de 3000 linhas
                        const PAGE_SIZE = 3000;
                        let currentTop = 0;
                        let pageId = 100;
                        
                        const fetchPage = () => {
                            ws.send(JSON.stringify({
                                "jsonrpc": "2.0", "id": pageId,
                                "method": "GetHyperCubeData",
                                "handle": objHandle,
                                "params": ["/qHyperCubeDef", [{
                                    "qTop": currentTop, "qLeft": 0,
                                    "qHeight": Math.min(PAGE_SIZE, totalRows - currentTop),
                                    "qWidth": totalCols
                                }]]
                            }));
                        };
                        
                        fetchPage();
                        
                        // Handler para paginação
                        const origHandler = ws.onmessage;
                        ws.onmessage = (event2) => {
                            const msg2 = JSON.parse(event2.data);
                            if (msg2.id >= 100 && msg2.result) {
                                const page = msg2.result[0];
                                const rows = (page.qMatrix || []).map(r => 
                                    r.map(c => c.qNum !== undefined && c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText)
                                );
                                allRows = allRows.concat(rows);
                                currentTop += rows.length;
                                
                                if (currentTop < totalRows) {
                                    pageId++;
                                    fetchPage();
                                } else {
                                    ws.close();
                                    resolve({ rows: allRows, totalRows, status: 'ok' });
                                }
                            }
                        };
                    }
                };
                
                ws.onerror = () => resolve({ rows: [], status: 'ws_error' });
                setTimeout(() => {
                    ws.close();
                    resolve({ rows: allRows, totalRows: allRows.length, status: 'timeout' });
                }, 45000);
            });
        }''';

        raw_res = await page.evaluate(query_js)
        await browser.close()

        elapsed = time.time() - t0
        status = raw_res.get('status', 'unknown')
        total_rows = raw_res.get('totalRows', 0)
        rows = raw_res.get('rows', [])

        print(f"  📡 Status: {status} | Registros: {len(rows)} / {total_rows} em {elapsed:.2f}s")
        return rows


def process_and_save(rows):
    """Processa linhas brutas do Qlik e gera JSON de realizado por linha × dia."""
    print("\n  3/3 Processando dados de setembro...")

    if not rows:
        print("  ⚠️ Nenhum dado retornado do Qlik (setembro ainda não começou ou sem dados).")
        # Gerar arquivo vazio para o dashboard funcionar
        empty = {'d_max': 0, 'linhas': {}, 'total_empresa_dia': [0.0] * 30, 'total_empresa_acum': [0.0] * 30}
        out_path = os.path.join(DATA_DIR, 'realizado_por_linha_dia.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(empty, f, ensure_ascii=False, indent=2)
        print(f"  💾 {out_path} (vazio)")
        return

    # Montar dicionário: {linha_nome: {dia: venda}}
    linhas_dict = {}
    d_max = 0

    for row in rows:
        if len(row) < 3:
            continue
        linha_nome = str(row[0]).strip()
        dia = int(row[1]) if isinstance(row[1], (int, float)) else int(str(row[1]).strip())
        venda = float(row[2]) if isinstance(row[2], (int, float)) else 0.0

        if dia > d_max:
            d_max = dia

        if linha_nome not in linhas_dict:
            linhas_dict[linha_nome] = {}
        linhas_dict[linha_nome][dia] = linhas_dict[linha_nome].get(dia, 0.0) + venda

    # Converter para arrays de 30 posições
    linhas_output = {}
    total_dia = [0.0] * 30
    total_acum = [0.0] * 30

    for linha_nome, dias_dict in linhas_dict.items():
        arr = [0.0] * 30
        for dia_num, venda in dias_dict.items():
            if 1 <= dia_num <= 30:
                arr[dia_num - 1] = round(venda, 2)
        linhas_output[linha_nome] = arr
        for i in range(30):
            total_dia[i] += arr[i]

    # Acumulado empresa
    acum = 0.0
    for i in range(30):
        acum += total_dia[i]
        total_acum[i] = round(acum, 2)
        total_dia[i] = round(total_dia[i], 2)

    result = {
        'd_max': d_max,
        'total_linhas_qlik': len(linhas_dict),
        'linhas': linhas_output,
        'total_empresa_dia': total_dia,
        'total_empresa_acum': total_acum
    }

    out_path = os.path.join(DATA_DIR, 'realizado_por_linha_dia.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    total_vendas = sum(total_dia[:d_max])
    print(f"  📊 {len(linhas_dict)} linhas com dados | D-Max: {d_max} | Total: R$ {total_vendas:,.2f}")
    print(f"  💾 {out_path}")


def main():
    rows = asyncio.run(fetch_qlik_setembro())
    process_and_save(rows)
    print("\n  🎉 Extração Qlik Setembro concluída!")


if __name__ == '__main__':
    main()
