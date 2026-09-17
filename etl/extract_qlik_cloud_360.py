"""
extract_qlik_cloud_360.py — Extrai os modelos completos de categorias, canais e hierarquias
do QLIK CLOUD (fsj.us.qlikcloud.com / Vendas Análise - Comparativo).

Substitui a extração legada On-Premises (que requeria VPN/rede corporativa), conectando
via WebSocket QIX Engine API com autenticação resiliente via Keycloak SSO e sessão persistente.

Gera em data/setembro/:
1. canais_summary.json (canais com vetores diários d26_07, d26_06, d25)
2. categorias_summary.json (grupos e subgrupos com totais e vetores diários)
3. hierarquia_detalhada.json (diretoria, distrital, grupo, subgrupo, linha)
4. canais_by_hierarquia.json (canais por hierarquia para filtros combinados)
5. filtro_hierarquia.json (listas distintas para multi-selects)
6. executive_kpis.json (KPIs executivos consolidados D-1)
"""
import os, sys, time, json, asyncio, datetime
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SETEMBRO_DIR = os.path.join(DATA_DIR, 'setembro')

QLIK_CLOUD_HOST = "fsj.us.qlikcloud.com"
APP_ID = "10fece07-9ab7-415c-89d6-e0a8c395aefe"  # Vendas Análise - Comparativo
HOME_URL = f"https://{QLIK_CLOUD_HOST}/analytics/home"

STORAGE_STATE_PATHS = [
    os.path.join(DATA_DIR, 'qlik_cloud_storage_state.json'),
    os.path.join(BASE_DIR, '..', 'Acompanhamento Categorias Digital', 'data', 'qlik_cloud_storage_state.json'),
    os.path.join(BASE_DIR, '..', 'Acompanhamento Online Canais Digitais', 'data', 'qlik_cloud_storage_state.json')
]

USERNAME = "lucas.alves6"
PASSWORD = "Eloise2025*"

DIGITAL_CHANNELS = "'SITE', 'APP', 'iFood', 'Figital', 'E-commerce', 'APP Tele Entrega', 'SITE Tele Entrega'"
TELE_CHANNELS = "'Venda Tele Entrega', 'Tele Encaminhada Lojas', 'Venda Tele Entrega Central', 'Tele Vizinhança'"
DT_CHANNELS = f"{DIGITAL_CHANNELS}, {TELE_CHANNELS}"

def clean_str(val):
    if val is None or str(val).strip() in ('', '-', 'NaN', 'None'): return ""
    return str(val).replace('\xa0', ' ').replace('\t', ' ').strip()

def calc_growth(cur, prev):
    diff = cur - prev
    pct = (diff / prev * 100.0) if prev > 0 else 0.0
    return round(pct, 2), round(diff, 2)

def get_channel_group(canal_name):
    c = str(canal_name).strip().upper()
    if c in ['APP', 'APP TELE ENTREGA', 'SITE', 'SITE TELE ENTREGA', 'IFOOD', 'RAPPI', 'FIGITAL', 'E-COMMERCE', 'E_COMMERCE']:
        return 'digital'
    elif c in ['TELE ENCAMINHADA LOJAS', 'TELE VIZINHANÇA', 'TELE VIZINHANÇAS', 'VENDA TELE ENTREGA', 'VENDA TELE ENTREGA CENTRAL']:
        return 'tele'
    else:
        return 'loja'

def find_valid_storage_state():
    for p in STORAGE_STATE_PATHS:
        if os.path.exists(p):
            return p
    return STORAGE_STATE_PATHS[0]

async def fetch_qlik_cloud_data():
    os.makedirs(SETEMBRO_DIR, exist_ok=True)
    t0 = time.time()
    print("=" * 70)
    print("  EXTRAÇÃO ACOMPANHAMENTO 360° — QLIK CLOUD SaaS (COMPARATIVO)")
    print("=" * 70)

    storage_path = find_valid_storage_state()
    print(f"Estado de sessão: {storage_path}")

    async with async_playwright() as p:
        print("1/4 Conectando ao Qlik Cloud via Playwright...")
        browser = await p.chromium.launch(headless=True)
        context_args = {'viewport': {'width': 1280, 'height': 800}, 'ignore_https_errors': True}
        if os.path.exists(storage_path):
            try:
                context = await browser.new_context(storage_state=storage_path, **context_args)
            except Exception:
                context = await browser.new_context(**context_args)
        else:
            context = await browser.new_context(**context_args)

        page = await context.new_page()
        print(f"Navegando para Qlik Cloud ({HOME_URL})...")
        await page.goto(HOME_URL, timeout=60000)

        # Login Keycloak se necessário
        try:
            user_input = await page.wait_for_selector('#username', timeout=12000)
            if user_input:
                print("Efetuando autenticação Keycloak SSO...")
                await page.fill('#username', USERNAME)
                await page.fill('#password', PASSWORD)
                await page.click('#kc-login')
                await page.wait_for_url(f"**{QLIK_CLOUD_HOST}/analytics/**", timeout=60000)
                print("✅ Autenticado com sucesso!")
                await page.wait_for_timeout(3000)
                await context.storage_state(path=storage_path)
        except Exception:
            print("Sessão ativa mantida.")

        await page.wait_for_timeout(3000)

        print("2/4 Executando extrações paginadas via WebSocket QIX Engine API...")
        queries_js = """async (cfg) => {
            const appId = cfg.appId;
            const digitalCh = cfg.digitalChannels;
            const dtCh = cfg.dtChannels;

            const csrfRes = await fetch('/api/v1/csrf-token');
            const csrfToken = csrfRes.headers.get('qlik-csrf-token');
            const wsUrl = `wss://${window.location.host}/app/${encodeURIComponent(appId)}?qlik-csrf-token=${csrfToken}`;

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

                async function fetchAllHyperCubeRows(objHandle, totalRows, qWidth) {
                    let rows = [];
                    let top = 0;
                    const pageSize = Math.floor(8000 / qWidth);
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

                ws.onmessage = (event) => {
                    const msg = JSON.parse(event.data);
                    if (msg.id && pending[msg.id]) {
                        const { res, rej } = pending[msg.id];
                        delete pending[msg.id];
                        if (msg.error) rej(new Error(JSON.stringify(msg.error)));
                        else res(msg);
                    }
                };

                ws.onopen = async () => {
                    try {
                        const openRes = await send("OpenDoc", -1, [appId]);
                        docHandle = openRes.result.qReturn.qHandle;

                        // 1. Canais x Dia (3 períodos)
                        const c1 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_canais_dia" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Canal Detalhado"] } },
                                    { "qDef": { "qFieldDefs": ["Dia Venda"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mês Venda]={'2026-09'}>} [Valor Mercadoria] - [Valor Devolução])", "qLabel": "v26_09" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mês Venda]={'2026-08'}>} [Valor Mercadoria] - [Valor Devolução])", "qLabel": "v26_08" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mês Venda]={'2025-09'}>} [Valor Mercadoria] - [Valor Devolução])", "qLabel": "v25_09" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 800, "qWidth": 5 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h1 = c1.result.qReturn.qHandle;
                        const l1 = await send("GetLayout", h1, []);
                        results.canais_dia = (l1.result.qLayout.qHyperCube.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));

                        // Descobrir maxDia fechado
                        const diasComVenda = new Set();
                        results.canais_dia.forEach(r => {
                            if (typeof r[2] === 'number' && r[2] > 0) diasComVenda.add(Number(r[1]));
                        });
                        const rawMaxDia = diasComVenda.size > 0 ? Math.max(...Array.from(diasComVenda)) : 1;
                        const today = new Date().getDate();
                        const maxDia = Math.max(1, Math.min(rawMaxDia, today > 1 ? today - 1 : rawMaxDia));
                        const dayFilter = `[Dia Venda]={"<=${maxDia}"}`;
                        results.maxDia = maxDia;

                        // 2. Categorias (Grupo x Subgrupo MTD)
                        const c2 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_cats" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Descrição Grupo"] } },
                                    { "qDef": { "qFieldDefs": ["Descrição SubGrupo"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-09'}, ${dayFilter}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "v26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-08'}, ${dayFilter}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "v26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2025-09'}, ${dayFilter}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "v25" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-09'}, ${dayFilter}, [Canal Detalhado]={${digitalCh}}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "vDig26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-08'}, ${dayFilter}, [Canal Detalhado]={${digitalCh}}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "vDig26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2025-09'}, ${dayFilter}, [Canal Detalhado]={${digitalCh}}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "vDig25" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-09'}, ${dayFilter}, [Canal Detalhado]={${dtCh}}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "vDt26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-08'}, ${dayFilter}, [Canal Detalhado]={${dtCh}}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "vDt26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2025-09'}, ${dayFilter}, [Canal Detalhado]={${dtCh}}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "vDt25" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 500, "qWidth": 11 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h2 = c2.result.qReturn.qHandle;
                        const l2 = await send("GetLayout", h2, []);
                        results.categorias = (l2.result.qLayout.qHyperCube.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));

                        // 3. Hierarquia Detalhada (Diretoria x Distrital x Grupo x Subgrupo x Linha MTD)
                        const c3 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_hier" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Diretoria"] } },
                                    { "qDef": { "qFieldDefs": ["Distrital"] } },
                                    { "qDef": { "qFieldDefs": ["Descrição Grupo"] } },
                                    { "qDef": { "qFieldDefs": ["Descrição SubGrupo"] } },
                                    { "qDef": { "qFieldDefs": ["Descrição Linha"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-09'}, ${dayFilter}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "v26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-08'}, ${dayFilter}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "v26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2025-09'}, ${dayFilter}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "v25" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-09'}, ${dayFilter}, [Canal Detalhado]={${digitalCh}}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "vDig26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-08'}, ${dayFilter}, [Canal Detalhado]={${digitalCh}}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "vDig26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2025-09'}, ${dayFilter}, [Canal Detalhado]={${digitalCh}}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "vDig25" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-09'}, ${dayFilter}, [Canal Detalhado]={${dtCh}}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "vDt26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-08'}, ${dayFilter}, [Canal Detalhado]={${dtCh}}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "vDt26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2025-09'}, ${dayFilter}, [Canal Detalhado]={${dtCh}}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "vDt25" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 500, "qWidth": 14 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h3 = c3.result.qReturn.qHandle;
                        const l3 = await send("GetLayout", h3, []);
                        const totalRows3 = l3.result.qLayout.qHyperCube.qSize.qcy;
                        console.log('Extraindo Hierarquia:', totalRows3, 'linhas...');
                        results.hierarquia = await fetchAllHyperCubeRows(h3, totalRows3, 14);

                        // 4. Canais por Hierarquia (Diretoria x Distrital x Grupo x Subgrupo x Linha x Canal MTD)
                        const c4 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_canais_hier" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Diretoria"] } },
                                    { "qDef": { "qFieldDefs": ["Distrital"] } },
                                    { "qDef": { "qFieldDefs": ["Descrição Grupo"] } },
                                    { "qDef": { "qFieldDefs": ["Descrição SubGrupo"] } },
                                    { "qDef": { "qFieldDefs": ["Descrição Linha"] } },
                                    { "qDef": { "qFieldDefs": ["Canal Detalhado"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-09'}, ${dayFilter}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "v26" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2026-08'}, ${dayFilter}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "v26_06" } },
                                    { "qDef": { "qDef": `Sum({1<[Ano-Mês Venda]={'2025-09'}, ${dayFilter}>} [Valor Mercadoria] - [Valor Devolução])`, "qLabel": "v25" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 800, "qWidth": 9 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h4 = c4.result.qReturn.qHandle;
                        const l4 = await send("GetLayout", h4, []);
                        const totalRows4 = l4.result.qLayout.qHyperCube.qSize.qcy;
                        console.log('Extraindo Canais x Hierarquia:', totalRows4, 'linhas...');
                        results.canais_hier = await fetchAllHyperCubeRows(h4, totalRows4, 9);

                        // 5. Linhas por Dia (para cálculo dinâmico dos vetores diários)
                        const c5 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_linhas_dia" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Descrição Linha"] } },
                                    { "qDef": { "qFieldDefs": ["Dia Venda"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mês Venda]={'2026-09'}>} [Valor Mercadoria] - [Valor Devolução])", "qLabel": "v26_dia" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mês Venda]={'2026-08'}>} [Valor Mercadoria] - [Valor Devolução])", "qLabel": "v26_06_dia" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mês Venda]={'2025-09'}>} [Valor Mercadoria] - [Valor Devolução])", "qLabel": "v25_dia" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 1000, "qWidth": 5 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h5 = c5.result.qReturn.qHandle;
                        const l5 = await send("GetLayout", h5, []);
                        const totalRows5 = l5.result.qLayout.qHyperCube.qSize.qcy;
                        results.linhas_dia = await fetchAllHyperCubeRows(h5, totalRows5, 5);

                        // 6. Grupos por Dia (para soma rápida no MTD)
                        const c6 = await send("CreateSessionObject", docHandle, [{
                            "qInfo": { "qType": "q_grupos_dia" },
                            "qHyperCubeDef": {
                                "qDimensions": [
                                    { "qDef": { "qFieldDefs": ["Descrição Grupo"] } },
                                    { "qDef": { "qFieldDefs": ["Dia Venda"] } }
                                ],
                                "qMeasures": [
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mês Venda]={'2026-09'}>} [Valor Mercadoria] - [Valor Devolução])", "qLabel": "v26_dia" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mês Venda]={'2026-08'}>} [Valor Mercadoria] - [Valor Devolução])", "qLabel": "v26_06_dia" } },
                                    { "qDef": { "qDef": "Sum({1<[Ano-Mês Venda]={'2025-09'}>} [Valor Mercadoria] - [Valor Devolução])", "qLabel": "v25_dia" } }
                                ],
                                "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 1000, "qWidth": 5 }],
                                "qSuppressZero": true, "qSuppressMissing": true
                            }
                        }]);
                        const h6 = c6.result.qReturn.qHandle;
                        const l6 = await send("GetLayout", h6, []);
                        results.grupos_dia = await fetchAllHyperCubeRows(h6, l6.result.qLayout.qHyperCube.qSize.qcy, 5);

                        ws.close();
                        resolve(results);
                    } catch(e) {
                        ws.close();
                        reject(new Error(String(e)));
                    }
                };
            });
        };"""

        cfg = {
            "appId": APP_ID,
            "digitalChannels": DIGITAL_CHANNELS,
            "dtChannels": DT_CHANNELS
        }

        cube_results = await page.evaluate(queries_js, cfg)
        print(f"  ✅ Extração WebSocket concluída em {time.time() - t0:.2f}s!")
        await browser.close()

    print("\n3/4 Processando matrizes e formatando modelos de dados...")
    max_dia = cube_results.get('maxDia', 15)

    # 1. Mapa diário de Linhas
    linhas_dia_map = {}
    for r in cube_results.get('linhas_dia', []):
        linha = clean_str(r[0])
        dia = int(r[1]) if str(r[1]).isdigit() else None
        if not linha or not dia or dia < 1 or dia > 31: continue
        if linha not in linhas_dia_map:
            linhas_dia_map[linha] = {'d26_07': [0.0]*31, 'd26_06': [0.0]*31, 'd25': [0.0]*31}
        linhas_dia_map[linha]['d26_07'][dia - 1] = round(float(r[2]) if isinstance(r[2], (int, float)) and not np.isnan(r[2]) else 0.0, 2)
        linhas_dia_map[linha]['d26_06'][dia - 1] = round(float(r[3]) if isinstance(r[3], (int, float)) and not np.isnan(r[3]) else 0.0, 2)
        linhas_dia_map[linha]['d25'][dia - 1] = round(float(r[4]) if isinstance(r[4], (int, float)) and not np.isnan(r[4]) else 0.0, 2)

    # 2. Mapa diário de Grupos
    grupos_dia_map = {}
    for r in cube_results.get('grupos_dia', []):
        grp = clean_str(r[0])
        dia = int(r[1]) if str(r[1]).isdigit() else None
        if not grp or not dia or dia < 1 or dia > 31: continue
        if grp not in grupos_dia_map:
            grupos_dia_map[grp] = {'d26_07': [0.0]*31, 'd26_06': [0.0]*31, 'd25': [0.0]*31}
        grupos_dia_map[grp]['d26_07'][dia - 1] = round(float(r[2]) if isinstance(r[2], (int, float)) and not np.isnan(r[2]) else 0.0, 2)
        grupos_dia_map[grp]['d26_06'][dia - 1] = round(float(r[3]) if isinstance(r[3], (int, float)) and not np.isnan(r[3]) else 0.0, 2)
        grupos_dia_map[grp]['d25'][dia - 1] = round(float(r[4]) if isinstance(r[4], (int, float)) and not np.isnan(r[4]) else 0.0, 2)

    # 3. Processar Canais Summary
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

    # 4. Processar Categorias Summary
    raw_cats = cube_results.get('categorias', [])
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

        grp_days = grupos_dia_map.get(grp, {'d26_07': [0.0]*31, 'd26_06': [0.0]*31, 'd25': [0.0]*31})

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
            'd25': grp_days['d25'], 'd26_06': grp_days['d26_06'], 'd26_07': grp_days['d26_07']
        })

    # 5. Processar Hierarquia Detalhada
    raw_hier = cube_results.get('hierarquia', [])
    hierarquia_detalhada = []
    for r in raw_hier:
        diretor = clean_str(r[0])
        distrital = clean_str(r[1])
        grp = clean_str(r[2])
        subgrp = clean_str(r[3])
        linha = clean_str(r[4])
        if not grp or not linha: continue

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

        linha_days = linhas_dia_map.get(linha, {'d26_07': [0.0]*31, 'd26_06': [0.0]*31, 'd25': [0.0]*31})

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
            'd25': linha_days['d25'], 'd26_06': linha_days['d26_06'], 'd26_07': linha_days['d26_07']
        })

    # 6. Processar Canais por Hierarquia
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

        linha_days = linhas_dia_map.get(linha, {'d26_07': [0.0]*31, 'd26_06': [0.0]*31, 'd25': [0.0]*31})

        canais_by_hierarquia.append({
            'diretor': diretor, 'distrital': distrital,
            'grupo': grp, 'subgrupo': subgrp, 'linha': linha,
            'canal': canal, 'canal_grupo': get_channel_group(canal),
            'v26': round(v26, 2), 'v26_06': round(v26_06, 2), 'v25': round(v25, 2)
        })

    # 7. Filtros de Hierarquia e Produto
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

    # 8. Executive KPIs
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

    executive_kpis = {
        "total_empresa": {
            "venda_jul_26": round(tot_mtd_26, 2),
            "venda_jun_26": round(tot_mtd_26_06, 2),
            "venda_jul_25": round(tot_mtd_25, 2),
            "mom_pct": mom_pct,
            "mom_rs": mom_rs,
            "yoy_pct": yoy_pct,
            "yoy_rs": yoy_rs
        },
        "digital": {
            "venda_jul_26": round(tot_dig_26, 2),
            "venda_jun_26": round(tot_dig_26_06, 2),
            "venda_jul_25": round(tot_dig_25, 2),
            "share_jul_26": round(tot_dig_26 / tot_mtd_26 * 100.0, 2) if tot_mtd_26 > 0 else 0.0,
            "mom_pct": calc_growth(tot_dig_26, tot_dig_26_06)[0],
            "yoy_pct": calc_growth(tot_dig_26, tot_dig_25)[0]
        },
        "digital_tele": {
            "venda_jul_26": round(tot_dt_26, 2),
            "venda_jun_26": round(tot_dt_26_06, 2),
            "venda_jul_25": round(tot_dt_25, 2),
            "share_jul_26": round(tot_dt_26 / tot_mtd_26 * 100.0, 2) if tot_mtd_26 > 0 else 0.0,
            "mom_pct": calc_growth(tot_dt_26, tot_dt_26_06)[0],
            "yoy_pct": calc_growth(tot_dt_26, tot_dt_25)[0]
        },
        "periodo_info": {
            "mes": "Setembro/2026",
            "tipo": "D-1 (Qlik Cloud SaaS)",
            "dias_fechados": max_dia,
            "periodo_str": f"01 a {max_dia:02d}/09/2026"
        }
    }

    print("\n4/4 Salvando arquivos JSON em data/setembro/...")
    with open(os.path.join(SETEMBRO_DIR, 'canais_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(canais_summary, f, ensure_ascii=False, indent=2)

    with open(os.path.join(SETEMBRO_DIR, 'categorias_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(categorias_summary, f, ensure_ascii=False, indent=2)

    with open(os.path.join(SETEMBRO_DIR, 'hierarquia_detalhada.json'), 'w', encoding='utf-8') as f:
        json.dump(hierarquia_detalhada, f, ensure_ascii=False, separators=(',', ':'))

    with open(os.path.join(SETEMBRO_DIR, 'canais_by_hierarquia.json'), 'w', encoding='utf-8') as f:
        json.dump(canais_by_hierarquia, f, ensure_ascii=False, separators=(',', ':'))

    with open(os.path.join(SETEMBRO_DIR, 'filtro_hierarquia.json'), 'w', encoding='utf-8') as f:
        json.dump(filtro_hierarquia, f, ensure_ascii=False, indent=2)

    with open(os.path.join(SETEMBRO_DIR, 'executive_kpis.json'), 'w', encoding='utf-8') as f:
        json.dump(executive_kpis, f, ensure_ascii=False, indent=2)

    # 9. Gerar e salvar realizado_por_linha_dia.json para compatibilidade com build_setembro_dashboard
    total_empresa_dia = [0.0] * 30
    for dia_idx in range(30):
        total_empresa_dia[dia_idx] = round(
            sum(c['d26_07'][dia_idx] for c in canais_dict.values()), 2
        )
    total_empresa_acum = []
    acum = 0.0
    for v in total_empresa_dia:
        acum += v
        total_empresa_acum.append(round(acum, 2))

    realizado_output = {
        'mes': 'Setembro/2026',
        'd_max': max_dia,
        'dias_com_venda': list(range(1, max_dia + 1)),
        'total_linhas_qlik': len(linhas_dia_map),
        'total_realizado_acum_dmax': total_empresa_acum[max_dia - 1] if max_dia > 0 else 0.0,
        'total_empresa_dia': total_empresa_dia,
        'total_empresa_acum': total_empresa_acum,
        'linhas': { l: data['d26_07'][:30] for l, data in linhas_dia_map.items() }
    }
    with open(os.path.join(SETEMBRO_DIR, 'realizado_por_linha_dia.json'), 'w', encoding='utf-8') as f:
        json.dump(realizado_output, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - t0
    print("=" * 70)
    print(f"  ✅ EXTRAÇÃO CONCLUÍDA COM SUCESSO EM {elapsed:.1f}s!")
    print(f"  Venda Total Empresa MTD: R$ {tot_mtd_26:,.2f}")
    print(f"  Venda Digital MTD:       R$ {tot_dig_26:,.2f} ({tot_dig_26/tot_mtd_26*100:.2f}%)")
    print(f"  Venda Digital+Tele MTD:  R$ {tot_dt_26:,.2f} ({tot_dt_26/tot_mtd_26*100:.2f}%)")
    print(f"  Dias Fechados:           01 a {max_dia:02d}/09/2026")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(fetch_qlik_cloud_data())
