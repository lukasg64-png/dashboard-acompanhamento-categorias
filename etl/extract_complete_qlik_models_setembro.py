"""
extract_complete_qlik_models_setembro.py — Extrai os modelos completos com fórmula oficial de Resultado Líquido
para Setembro/2026 (Set/26 vs Ago/26 vs Set/25) via WebSocket do Qlik Sense Engine.
"""
import os, sys, time, json, asyncio, datetime
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SETEMBRO_DIR = os.path.join(DATA_DIR, 'setembro')

QLIK_URL = "https://sense.farmaciassaojoao.com.br"
APP_ID = "671fa4f4-eb7d-418f-b4c9-936e87d8011d"
SHEET_ID = "ddd70c77-1a06-40d9-aff2-efa4b6b67b24"
SHEET_URL = f"{QLIK_URL}/sense/app/{APP_ID}/sheet/{SHEET_ID}/state/analysis"

USERNAME = "lucas.alves6"
PASSWORD = "Eloise2025*"

def clean_str(val):
    if pd.isna(val) or val is None or str(val).strip() == '-': return ""
    return str(val).replace('\xa0', ' ').replace('\t', ' ').strip()

def calc_growth(cur, prev):
    diff = cur - prev
    pct = (diff / prev * 100.0) if prev > 0 else 0.0
    return round(pct, 2), round(diff, 2)

def get_channel_group(canal_name):
    c = str(canal_name).strip().upper()
    if c in ['APP', 'APP TELE ENTREGA', 'SITE TELE ENTREGA', 'E_COMMERCE', 'E-COMMERCE', 'IFOOD', 'RAPPI', 'SITE']:
        return 'digital'
    elif c in ['TELE ENCAMINHADA LOJAS', 'TELE VIZINHANÇA', 'TELE VIZINHANÇAS', 'VENDA TELE ENTREGA', 'VENDA TELE ENTREGA CENTRAL']:
        return 'tele'
    else:
        return 'loja'

async def fetch_all_qlik_cubes():
    os.makedirs(SETEMBRO_DIR, exist_ok=True)
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  EXTRAINDO MODELOS COMPLETOS DO QLIK SENSE — SETEMBRO/2026")
    print("=" * 70)

    async with async_playwright() as p:
        print("  1/4 Conectando ao Qlik Sense...")
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
        
        print("  2/4 Executando extração paginada no Qlik Engine...")
        queries_js = '''async () => {
            const wsUrl = `wss://${window.location.host}/app/${encodeURIComponent('671fa4f4-eb7d-418f-b4c9-936e87d8011d')}?reloadUri=https://${window.location.host}/`;
            
            return new Promise((resolve, reject) => {
                const ws = new WebSocket(wsUrl);
                let docHandle = null;
                const results = {};
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
                        
                        // 1. Canais x Dia (3 períodos: Set/26, Ago/26, Set/25)
                        const c1 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_canais_dia_3p_set" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Canal"] } },
                                    { "qDef": { "qFieldDefs": ["Dia"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-09'}>} [Receita Líquida])", "qLabel": "Set_26" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-08'}>} [Receita Líquida])", "qLabel": "Ago_26" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2025-09'}>} [Receita Líquida])", "qLabel": "Set_25" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 1000, "qWidth": 5 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h1 = c1.result.qReturn.qHandle;
                        const l1 = await send("GetLayout", h1, []);
                        results.canais_dia = (l1.result.qLayout.qHyperCube.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));
                        
                        const diasComVenda = new Set();
                        results.canais_dia.forEach(r => {
                            if (typeof r[2] === 'number' && r[2] > 0) diasComVenda.add(Number(r[1]));
                        });
                        const rawMaxDia = diasComVenda.size > 0 ? Math.max(...Array.from(diasComVenda)) : 1;
                        const today = new Date().getDate();
                        const maxDia = Math.max(1, Math.min(rawMaxDia, today > 1 ? today - 1 : rawMaxDia));
                        const dayFilter = `[Dia]={"<=${maxDia}"}`;
                        
                        // 2. Categorias (Grupo + Subgrupo) com 9 medidas (MTD)
                        const c2 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_cats_9m_set" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Desc_Grupo"] } },
                                    { "qDef": { "qFieldDefs": ["Desc_Subgrupo"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-09'}, ${dayFilter}>} [Receita Líquida])`, "qLabel": "v26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-08'}, ${dayFilter}>} [Receita Líquida])`, "qLabel": "v26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2025-09'}, ${dayFilter}>} [Receita Líquida])`, "qLabel": "v25" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-09'}, ${dayFilter}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL'}>} [Receita Líquida])`, "qLabel": "vDig26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-08'}, ${dayFilter}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL'}>} [Receita Líquida])`, "qLabel": "vDig26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2025-09'}, ${dayFilter}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL'}>} [Receita Líquida])`, "qLabel": "vDig25" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-09'}, ${dayFilter}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL','TELE ENTREGA','TELE VENDA'}>} [Receita Líquida])`, "qLabel": "vDt26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-08'}, ${dayFilter}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL','TELE ENTREGA','TELE VENDA'}>} [Receita Líquida])`, "qLabel": "vDt26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2025-09'}, ${dayFilter}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL','TELE ENTREGA','TELE VENDA'}>} [Receita Líquida])`, "qLabel": "vDt25" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 500, "qWidth": 11 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h2 = c2.result.qReturn.qHandle;
                        const l2 = await send("GetLayout", h2, []);
                        results.categorias = (l2.result.qLayout.qHyperCube.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));
                        
                        // 3. Hierarquia (Diretor + Distrital + Grupo + Subgrupo + Linha) com 9 medidas (Paginado MTD)
                        const c3 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_hier_9m_set" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Diretor"] } },
                                    { "qDef": { "qFieldDefs": ["Distrital"] } },
                                    { "qDef": { "qFieldDefs": ["Desc_Grupo"] } },
                                    { "qDef": { "qFieldDefs": ["Desc_Subgrupo"] } },
                                    { "qDef": { "qFieldDefs": ["Desc_Linha"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-09'}, ${dayFilter}>} [Receita Líquida])`, "qLabel": "v26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-08'}, ${dayFilter}>} [Receita Líquida])`, "qLabel": "v26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2025-09'}, ${dayFilter}>} [Receita Líquida])`, "qLabel": "v25" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-09'}, ${dayFilter}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL'}>} [Receita Líquida])`, "qLabel": "vDig26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-08'}, ${dayFilter}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL'}>} [Receita Líquida])`, "qLabel": "vDig26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2025-09'}, ${dayFilter}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL'}>} [Receita Líquida])`, "qLabel": "vDig25" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-09'}, ${dayFilter}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL','TELE ENTREGA','TELE VENDA'}>} [Receita Líquida])`, "qLabel": "vDt26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-08'}, ${dayFilter}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL','TELE ENTREGA','TELE VENDA'}>} [Receita Líquida])`, "qLabel": "vDt26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2025-09'}, ${dayFilter}, [Canal]={'APP','SITE','IFOOD','MERCADO LIVRE','RAPPI','PARCEIROS','IFOOD ULTRA','SUPERFACIL','TELE ENTREGA','TELE VENDA'}>} [Receita Líquida])`, "qLabel": "vDt25" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 800, "qWidth": 14 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h3 = c3.result.qReturn.qHandle;
                        const l3 = await send("GetLayout", h3, []);
                        const totalRows3 = l3.result.qLayout.qHyperCube.qSize.qcy;
                        results.hierarquia = await fetchAllHyperCubeRows(h3, totalRows3, 14, 500);
                        
                        // 4. Canais por Hierarquia (Diretor + Distrital + Grupo + Subgrupo + Linha + Canal) (Paginado MTD)
                        const c4 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_canais_hier_3p_set" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Diretor"] } },
                                    { "qDef": { "qFieldDefs": ["Distrital"] } },
                                    { "qDef": { "qFieldDefs": ["Desc_Grupo"] } },
                                    { "qDef": { "qFieldDefs": ["Desc_Subgrupo"] } },
                                    { "qDef": { "qFieldDefs": ["Desc_Linha"] } },
                                    { "qDef": { "qFieldDefs": ["Canal"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-09'}, ${dayFilter}>} [Receita Líquida])`, "qLabel": "v26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2026-08'}, ${dayFilter}>} [Receita Líquida])`, "qLabel": "v26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mes]={'2025-09'}, ${dayFilter}>} [Receita Líquida])`, "qLabel": "v25" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 1000, "qWidth": 9 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h4 = c4.result.qReturn.qHandle;
                        const l4 = await send("GetLayout", h4, []);
                        const totalRows4 = l4.result.qLayout.qHyperCube.qSize.qcy;
                        results.canais_hier = await fetchAllHyperCubeRows(h4, totalRows4, 9, 1000);
                        
                        ws.close();
                        resolve(results);
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
        
        cube_results = await page.evaluate(queries_js)
        print(f"  ✅ Extração no Qlik Engine concluída em {time.time() - t0:.2f}s!")
        await browser.close()

    t_proc = time.time()
    print("\n  3/4 Processando matrizes e calculando modelos de dados...")

    # 1. Processar Canais Summary
    raw_canais_dia = cube_results.get('canais_dia', [])
    canais_dict = {}
    for r in raw_canais_dia:
        canal = clean_str(r[0])
        dia = int(r[1]) if str(r[1]).isdigit() else None
        if not canal or not dia or dia < 1 or dia > 31: continue
        
        v26_d = float(r[2]) if isinstance(r[2], (int, float)) and not np.isnan(r[2]) else 0.0
        v26_06_d = float(r[3]) if isinstance(r[3], (int, float)) and not np.isnan(r[3]) else 0.0
        v25_d = float(r[4]) if isinstance(r[4], (int, float)) and not np.isnan(r[4]) else 0.0
        
        if canal not in canais_dict:
            canais_dict[canal] = {
                'canal': canal, 'grupo': get_channel_group(canal),
                'venda_jul_26': 0.0, 'venda_jun_26': 0.0, 'venda_jul_25': 0.0,
                'd26_07': [0.0]*31, 'd26_06': [0.0]*31, 'd25': [0.0]*31
            }
        
        canais_dict[canal]['d26_07'][dia - 1] = round(v26_d, 2)
        canais_dict[canal]['d26_06'][dia - 1] = round(v26_06_d, 2)
        canais_dict[canal]['d25'][dia - 1] = round(v25_d, 2)

    # Identificar último dia com dados de Setembro — D-1
    dias_com_venda = [i+1 for i in range(31) if any(c['d26_07'][i] > 0 for c in canais_dict.values())]
    raw_max_dia = max(dias_com_venda) if dias_com_venda else 1
    today = datetime.date.today().day
    max_dia = max(1, min(raw_max_dia, today - 1 if today > 1 else raw_max_dia))

    # Consolidar totais MTD dos canais (01 a max_dia)
    for c in canais_dict.values():
        c['venda_jul_26'] = round(sum(c['d26_07'][:max_dia]), 2)
        c['venda_jun_26'] = round(sum(c['d26_06'][:max_dia]), 2)
        c['venda_jul_25'] = round(sum(c['d25'][:max_dia]), 2)

    total_v26 = sum(c['venda_jul_26'] for c in canais_dict.values())
    total_v26_06 = sum(c['venda_jun_26'] for c in canais_dict.values())
    total_v25 = sum(c['venda_jul_25'] for c in canais_dict.values())

    canais_summary = []
    for c in canais_dict.values():
        m_pct, m_rs = calc_growth(c['venda_jul_26'], c['venda_jun_26'])
        y_pct, y_rs = calc_growth(c['venda_jul_26'], c['venda_jul_25'])
        c['mom_pct'] = m_pct
        c['mom_rs'] = m_rs
        c['yoy_pct'] = y_pct
        c['yoy_rs'] = y_rs
        
        part_26 = round((c['venda_jul_26'] / total_v26 * 100.0), 2) if total_v26 > 0 else 0.0
        part_jun = round((c['venda_jun_26'] / total_v26_06 * 100.0), 2) if total_v26_06 > 0 else 0.0
        part_25 = round((c['venda_jul_25'] / total_v25 * 100.0), 2) if total_v25 > 0 else 0.0
        c['part_jul_26'] = part_26
        c['part_jun_26'] = part_jun
        c['part_jul_25'] = part_25
        c['var_pp'] = round(part_26 - part_25, 2)
        canais_summary.append(c)

    canais_summary.sort(key=lambda x: x['venda_jul_26'], reverse=True)

    # 2. Processar Categorias Summary
    raw_cats = cube_results.get('categorias', [])
    raw_hier = cube_results.get('hierarquia', [])
    categorias_summary = []
    for r in raw_cats:
        grp = clean_str(r[0])
        subgrp = clean_str(r[1])
        if not grp: continue
        
        v26 = float(r[2]) if isinstance(r[2], (int, float)) and not np.isnan(r[2]) else 0.0
        v26_06 = float(r[3]) if isinstance(r[3], (int, float)) and not np.isnan(r[3]) else 0.0
        v25 = float(r[4]) if isinstance(r[4], (int, float)) and not np.isnan(r[4]) else 0.0
        
        vDig26 = float(r[5]) if isinstance(r[5], (int, float)) and not np.isnan(r[5]) else 0.0
        vDig26_06 = float(r[6]) if isinstance(r[6], (int, float)) and not np.isnan(r[6]) else 0.0
        vDig25 = float(r[7]) if isinstance(r[7], (int, float)) and not np.isnan(r[7]) else 0.0
        
        vDt26 = float(r[8]) if isinstance(r[8], (int, float)) and not np.isnan(r[8]) else 0.0
        vDt26_06 = float(r[9]) if isinstance(r[9], (int, float)) and not np.isnan(r[9]) else 0.0
        vDt25 = float(r[10]) if isinstance(r[10], (int, float)) and not np.isnan(r[10]) else 0.0
        
        m_pct, m_rs = calc_growth(v26, v26_06)
        y_pct, y_rs = calc_growth(v26, v25)
        
        part_26 = round((v26 / total_v26 * 100.0), 2) if total_v26 > 0 else 0.0
        part_jun = round((v26_06 / total_v26_06 * 100.0), 2) if total_v26_06 > 0 else 0.0
        part_25 = round((v25 / total_v25 * 100.0), 2) if total_v25 > 0 else 0.0
        
        categorias_summary.append({
            'diretor': '', 'distrital': '',
            'grupo': grp, 'subgrupo': subgrp,
            'venda_jul_26': round(v26, 2),
            'venda_jun_26': round(v26_06, 2),
            'venda_jul_25': round(v25, 2),
            'venda_digital_jul_26': round(vDig26, 2),
            'venda_digital_jun_26': round(vDig26_06, 2),
            'venda_digital_jul_25': round(vDig25, 2),
            'venda_dt_jul_26': round(vDt26, 2),
            'venda_dt_jun_26': round(vDt26_06, 2),
            'venda_dt_jul_25': round(vDt25, 2),
            'mom_pct': m_pct, 'mom_rs': m_rs,
            'yoy_pct': y_pct, 'yoy_rs': y_rs,
            'part_jul_26': part_26, 'part_jun_26': part_jun, 'part_jul_25': part_25,
            'var_pp': round(part_26 - part_25, 2),
            'd25': [0.0]*31, 'd26_06': [0.0]*31, 'd26_07': [0.0]*31
        })

    # 3. Processar Hierarquia Detalhada (com Diretor e Distrital)
    hierarquia_detalhada = []
    for r in raw_hier:
        diretor = clean_str(r[0])
        distrital = clean_str(r[1])
        grp = clean_str(r[2])
        subgrp = clean_str(r[3])
        linha = clean_str(r[4])
        if not grp: continue
        
        v26 = float(r[5]) if isinstance(r[5], (int, float)) and not np.isnan(r[5]) else 0.0
        v26_06 = float(r[6]) if isinstance(r[6], (int, float)) and not np.isnan(r[6]) else 0.0
        v25 = float(r[7]) if isinstance(r[7], (int, float)) and not np.isnan(r[7]) else 0.0
        
        vDig26 = float(r[8]) if isinstance(r[8], (int, float)) and not np.isnan(r[8]) else 0.0
        vDig26_06 = float(r[9]) if isinstance(r[9], (int, float)) and not np.isnan(r[9]) else 0.0
        vDig25 = float(r[10]) if isinstance(r[10], (int, float)) and not np.isnan(r[10]) else 0.0
        
        vDt26 = float(r[11]) if isinstance(r[11], (int, float)) and not np.isnan(r[11]) else 0.0
        vDt26_06 = float(r[12]) if isinstance(r[12], (int, float)) and not np.isnan(r[12]) else 0.0
        vDt25 = float(r[13]) if isinstance(r[13], (int, float)) and not np.isnan(r[13]) else 0.0
        
        m_pct, m_rs = calc_growth(v26, v26_06)
        y_pct, y_rs = calc_growth(v26, v25)
        
        hierarquia_detalhada.append({
            'diretor': diretor, 'distrital': distrital,
            'grupo': grp, 'subgrupo': subgrp, 'linha': linha,
            'venda_jul_26': round(v26, 2),
            'venda_jun_26': round(v26_06, 2),
            'venda_jul_25': round(v25, 2),
            'venda_digital_jul_26': round(vDig26, 2),
            'venda_digital_jun_26': round(vDig26_06, 2),
            'venda_digital_jul_25': round(vDig25, 2),
            'venda_dt_jul_26': round(vDt26, 2),
            'venda_dt_jun_26': round(vDt26_06, 2),
            'venda_dt_jul_25': round(vDt25, 2),
            'mom_pct': m_pct, 'mom_rs': m_rs,
            'yoy_pct': y_pct, 'yoy_rs': y_rs,
            'd25': [0.0]*31, 'd26_06': [0.0]*31, 'd26_07': [0.0]*31
        })

    # 4. Processar Canais por Hierarquia (com Diretor e Distrital)
    raw_ch_hier = cube_results.get('canais_hier', [])
    canais_by_hierarquia = []
    for r in raw_ch_hier:
        diretor = clean_str(r[0])
        distrital = clean_str(r[1])
        grp = clean_str(r[2])
        subgrp = clean_str(r[3])
        linha = clean_str(r[4])
        canal = clean_str(r[5])
        if not grp or not canal: continue
        
        v26 = float(r[6]) if isinstance(r[6], (int, float)) and not np.isnan(r[6]) else 0.0
        v26_06 = float(r[7]) if isinstance(r[7], (int, float)) and not np.isnan(r[7]) else 0.0
        v25 = float(r[8]) if isinstance(r[8], (int, float)) and not np.isnan(r[8]) else 0.0
        
        canais_by_hierarquia.append({
            'diretor': diretor, 'distrital': distrital,
            'grupo': grp, 'subgrupo': subgrp, 'linha': linha,
            'canal': canal, 'canal_grupo': get_channel_group(canal),
            'v26': round(v26, 2), 'v26_06': round(v26_06, 2), 'v25': round(v25, 2),
            'd25': [0.0]*31, 'd26_06': [0.0]*31, 'd26_07': [0.0]*31
        })

    # 5. Gerar Filtros de Hierarquia e Produto
    diretores_set = sorted(list(set(h['diretor'] for h in hierarquia_detalhada if h.get('diretor'))))
    distritais_set = sorted(list(set(h['distrital'] for h in hierarquia_detalhada if h.get('distrital'))))
    grupos_set = sorted(list(set(c['grupo'] for c in categorias_summary if c.get('grupo'))))
    subgrupos_set = sorted(list(set(c['subgrupo'] for c in categorias_summary if c.get('subgrupo'))))
    linhas_set = sorted(list(set(h['linha'] for h in hierarquia_detalhada if h.get('linha'))))

    filtro_hierarquia = {
        'diretores': diretores_set,
        'distritais': distritais_set,
        'coordenadores': [],
        'grupos': grupos_set,
        'subgrupos': subgrupos_set,
        'linhas': linhas_set,
        'laboratorios': []
    }

    # 6. Gerar Executive KPIs (MTD Comparativo: 01 a max_dia)
    tot_mtd_26 = sum(sum(c['d26_07'][:max_dia]) for c in canais_summary)
    tot_mtd_26_06 = sum(sum(c['d26_06'][:max_dia]) for c in canais_summary)
    tot_mtd_25 = sum(sum(c['d25'][:max_dia]) for c in canais_summary)

    tot_dig_26 = sum(sum(c['d26_07'][:max_dia]) for c in canais_summary if c['grupo'] == 'digital')
    tot_dig_26_06 = sum(sum(c['d26_06'][:max_dia]) for c in canais_summary if c['grupo'] == 'digital')
    tot_dig_25 = sum(sum(c['d25'][:max_dia]) for c in canais_summary if c['grupo'] == 'digital')

    tot_dt_26 = sum(sum(c['d26_07'][:max_dia]) for c in canais_summary if c['grupo'] in ['digital', 'tele'])
    tot_dt_26_06 = sum(sum(c['d26_06'][:max_dia]) for c in canais_summary if c['grupo'] in ['digital', 'tele'])
    tot_dt_25 = sum(sum(c['d25'][:max_dia]) for c in canais_summary if c['grupo'] in ['digital', 'tele'])

    mom_pct, mom_rs = calc_growth(tot_mtd_26, tot_mtd_26_06)
    yoy_pct, yoy_rs = calc_growth(tot_mtd_26, tot_mtd_25)

    dig_mom_pct, dig_mom_rs = calc_growth(tot_dig_26, tot_dig_26_06)
    dig_yoy_pct, dig_yoy_rs = calc_growth(tot_dig_26, tot_dig_25)

    dt_mom_pct, dt_mom_rs = calc_growth(tot_dt_26, tot_dt_26_06)
    dt_yoy_pct, dt_yoy_rs = calc_growth(tot_dt_26, tot_dt_25)

    executive_kpis = {
        'total_empresa': {
            'venda_jul_26': round(tot_mtd_26, 2),
            'venda_jun_26': round(tot_mtd_26_06, 2),
            'venda_jul_25': round(tot_mtd_25, 2),
            'mom_pct': mom_pct, 'mom_rs': mom_rs,
            'yoy_pct': yoy_pct, 'yoy_rs': yoy_rs
        },
        'digital': {
            'venda_jul_26': round(tot_dig_26, 2),
            'venda_jun_26': round(tot_dig_26_06, 2),
            'venda_jul_25': round(tot_dig_25, 2),
            'share_jul_26': round(tot_dig_26 / tot_mtd_26 * 100.0, 2) if tot_mtd_26 > 0 else 0.0,
            'mom_pct': dig_mom_pct, 'yoy_pct': dig_yoy_pct
        },
        'digital_tele': {
            'venda_jul_26': round(tot_dt_26, 2),
            'venda_jun_26': round(tot_dt_26_06, 2),
            'venda_jul_25': round(tot_dt_25, 2),
            'share_jul_26': round(tot_dt_26 / tot_mtd_26 * 100.0, 2) if tot_mtd_26 > 0 else 0.0,
            'mom_pct': dt_mom_pct, 'yoy_pct': dt_yoy_pct
        },
        'periodo_info': {
            'mes': 'Setembro/2026',
            'tipo': 'D-1 (Qlik Sense Enterprise)',
            'dias_fechados': max_dia,
            'periodo_str': f'01 a {max_dia:02d}/09/2026' if max_dia > 1 else '01/09/2026'
        }
    }

    # Salvar todos os arquivos JSON em data/setembro/
    def save_json(data, name):
        p = os.path.join(SETEMBRO_DIR, name)
        if name == 'canais_by_hierarquia.json' and isinstance(data, list):
            compact = []
            for item in data:
                o = dict(item)
                if 'd25' in o and all(v == 0 for v in o['d25']): del o['d25']
                if 'd26_06' in o and all(v == 0 for v in o['d26_06']): del o['d26_06']
                if 'd26_07' in o and all(v == 0 for v in o['d26_07']): del o['d26_07']
                compact.append(o)
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(compact, f, ensure_ascii=False, separators=(',', ':'))
            return
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    save_json(canais_summary, 'canais_summary.json')
    save_json(categorias_summary, 'categorias_summary.json')
    save_json(hierarquia_detalhada, 'hierarquia_detalhada.json')
    save_json(canais_by_hierarquia, 'canais_by_hierarquia.json')
    save_json(filtro_hierarquia, 'filtro_hierarquia.json')
    save_json(executive_kpis, 'executive_kpis.json')

    print(f"  4/4 Todos os JSONs de Setembro salvos com sucesso em {time.time() - t_proc:.2f}s!")
    print(f"  📊 Total Setembro D-1 (01 a {max_dia:02d}): R$ {total_v26:,.2f} | YoY: {yoy_pct:+.1f}% | MoM: {mom_pct:+.1f}%")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    asyncio.run(fetch_all_qlik_cubes())
