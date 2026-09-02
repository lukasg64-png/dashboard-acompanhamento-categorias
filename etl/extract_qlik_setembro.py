"""
extract_qlik_setembro.py — Extrai dados de venda D-1 do Qlik Sense para Setembro/2026.
Query: Desc_Linha × Dia.
Gera JSON com realizado por linha × dia para comparar com as metas de Setembro/2026.
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
        print("  Carregando pasta do Qlik Sense...")
        await page.goto(SHEET_URL, timeout=60000)
        try:
            await page.wait_for_selector('.qv-panel-sheet', timeout=45000)
        except Exception:
            await page.wait_for_timeout(12000)
        await page.wait_for_timeout(5000)

        print("  2/3 Executando query Desc_Linha × Dia (Set/2026)...")

        query_js = '''async () => {
            const wsUrl = `wss://${window.location.host}/app/${encodeURIComponent('671fa4f4-eb7d-418f-b4c9-936e87d8011d')}?reloadUri=https://${window.location.host}/`;
            
            return new Promise((resolve, reject) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
                let msgId = 1;
                const pending = {};
                
                function send(method, handle, params) {
                    return new Promise((res, rej) => {
                        const id = msgId++;
                        pending[id] = { res, rej };
                        ws.send(JSON.stringify({ "jsonrpc": "2.0", "id": id, "method": method, "handle": handle, "params": params }));
                    });
                }
                
                async function fetchAllHyperCubeRows(objHandle, totalRows, qWidth, pageSize) {
                    let rows = [];
                    let top = 0;
                    while (top < totalRows) {
                        const height = Math.min(pageSize, totalRows - top);
                        const pageRes = await send("GetHyperCubeData", objHandle, ["/qHyperCubeDef", [{ "qTop": top, "qLeft": 0, "qHeight": height, "qWidth": qWidth }]]);
                        const matrix = pageRes.result.qDataPages[0]?.qMatrix || [];
                        if (matrix.length === 0) break;
                        matrix.forEach(r => rows.push(r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText)));
                        top += matrix.length;
                    }
                    return rows;
                }
                
                ws.onopen = async () => {
                    try {
                        const openRes = await send("OpenDoc", -1, ["671fa4f4-eb7d-418f-b4c9-936e87d8011d"]);
                        docHandle = openRes.result.qReturn.qHandle;
                        
                        const c1 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_set_linha_dia" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Desc_Linha"] } },
                                    { "qDef": { "qFieldDefs": ["Dia"] } }
                                ],
                                "qMeasures": [{
                                    "qDef": {
                                        "qDef": "Sum({1<[Ano-Mes]={'2026-09'}>} [Receita Líquida])",
                                        "qLabel": "Venda Set26"
                                    }
                                }],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 1000, "qWidth": 3 }],
                                "qSuppressZero": true,
                                "qSuppressMissing": true
                            }
                        }]);
                        const h1 = c1.result.qReturn.qHandle;
                        const l1 = await send("GetLayout", h1, []);
                        const totalRows = l1.result.qLayout.qHyperCube.qSize.qcy;
                        const allRows = await fetchAllHyperCubeRows(h1, totalRows, 3, 1000);
                        
                        ws.close();
                        resolve({ rows: allRows, totalRows: totalRows, status: 'ok' });
                    } catch (e) {
                        ws.close();
                        reject(new Error(e.message || String(e)));
                    }
                };
                
                ws.onmessage = (event) => {
                    const msg = JSON.parse(event.data);
                    if (msg.id && pending[msg.id]) {
                        const { res, rej } = pending[msg.id];
                        delete pending[msg.id];
                        if (msg.error) rej(new Error(JSON.stringify(msg.error)));
                        else res(msg);
                    }
                };
            });
        };'''

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
        print("  ⚠️ Nenhum dado retornado do Qlik.")
        return None

    # Estrutura: { linha: [dia1, dia2, ..., dia30] }
    linhas_dict = {}
    dias_com_venda = set()

    for r in rows:
        if len(r) < 3: continue
        linha_nome = str(r[0]).strip().upper() if r[0] else ''
        dia_val = r[1]
        venda_val = r[2]

        if not linha_nome or dia_val is None:
            continue

        try:
            dia = int(dia_val)
        except (ValueError, TypeError):
            continue

        if dia < 1 or dia > 30:
            continue

        try:
            venda = float(venda_val) if venda_val not in (None, '', '-') else 0.0
        except (ValueError, TypeError):
            venda = 0.0

        if linha_nome not in linhas_dict:
            linhas_dict[linha_nome] = [0.0] * 30

        linhas_dict[linha_nome][dia - 1] += round(venda, 2)
        if venda > 0:
            dias_com_venda.add(dia)

    d_max = max(dias_com_venda) if dias_com_venda else 0
    # D-1: se hoje é dia D e temos dados de D, ignorar D (dados parciais)
    from datetime import date
    today_day = date.today().day
    if d_max >= today_day and today_day > 1:
        d_max = today_day - 1

    # Totais diários da empresa
    total_empresa_dia = [0.0] * 30
    for dia_idx in range(30):
        total_empresa_dia[dia_idx] = round(
            sum(linhas_dict[l][dia_idx] for l in linhas_dict), 2
        )

    # Acumulados diários da empresa
    total_empresa_acum = []
    acum = 0.0
    for v in total_empresa_dia:
        acum += v
        total_empresa_acum.append(round(acum, 2))

    total_realizado_dmax = total_empresa_acum[d_max - 1] if d_max > 0 else 0.0

    output = {
        'mes': 'Setembro/2026',
        'd_max': d_max,
        'dias_com_venda': sorted(list(dias_com_venda)),
        'total_linhas_qlik': len(linhas_dict),
        'total_realizado_acum_dmax': total_realizado_dmax,
        'total_empresa_dia': total_empresa_dia,
        'total_empresa_acum': total_empresa_acum,
        'linhas': linhas_dict
    }

    out_path = os.path.join(DATA_DIR, 'realizado_por_linha_dia.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  📅 D-Max fechado: Dia {d_max} (Setembro/2026)")
    print(f"  🏢 Total Realizado Acumulado (D1..D{d_max}): R$ {total_realizado_dmax:,.2f}")
    print(f"  📦 Linhas com venda: {len(linhas_dict)}")
    print(f"  💾 Salvo em: {out_path}")

    return output


def main():
    rows = asyncio.run(fetch_qlik_setembro())
    process_and_save(rows)
    print("\n  🎉 Extração Qlik Setembro concluída!")


if __name__ == '__main__':
    main()
