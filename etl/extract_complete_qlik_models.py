"""
extract_complete_qlik_models.py — Extrai os modelos completos com fórmula exata de Resultado Líquido
e vetores diários de 31 dias para Agosto/2026, Julho/2026 e Agosto/2025 diretamente do Qlik Sense Engine API.
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
    os.makedirs(AGOSTO_DIR, exist_ok=True)
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  EXTRAINDO MODELOS COMPLETOS DO QLIK SENSE COM FÓRMULA OFICIAL")
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
        await page.goto(SHEET_URL, timeout=60000)
        await page.wait_for_timeout(8000)
        
        print("  2/4 Executando HyperCubes diários no Qlik Engine...")
        queries_js = '''async () => {
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
                        
                        // 1. Canais x Dia (3 períodos)
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 10,
                            "method": "CreateSessionObject",
                            "handle": docHandle,
                            "params": [{
                                "qInfo": { "qType": "q_canais_dia_3p" },
                                "qHyperCubeDef": {
                                    "qDimensions": [
                                        { "qDef": { "qFieldDefs": ["Canal"] } },
                                        { "qDef": { "qFieldDefs": ["Dia"] } }
                                    ],
                                    "qMeasures": [
                                        { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-08'}>} [Receita Líquida])", "qLabel": "Ago_26" } },
                                        { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-07'}>} [Receita Líquida])", "qLabel": "Jul_26" } },
                                        { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2025-08'}>} [Receita Líquida])", "qLabel": "Ago_25" } }
                                    ],
                                    "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 1000, "qWidth": 5 }],
                                    "qSuppressZero": true, "qSuppressMissing": true
                                }
                            }]
                        }));
                    } else if (msg.id === 10 && msg.result) {
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 11,
                            "method": "GetLayout",
                            "handle": msg.result.qReturn.qHandle,
                            "params": []
                        }));
                    } else if (msg.id === 11 && msg.result) {
                        const hc = msg.result.qLayout.qHyperCube;
                        results.canais_dia = (hc.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));
                        
                        // 2. Categorias (Grupo + Subgrupo) x Dia (3 períodos)
                        // Max 10.000 cells -> Width 5 -> Height 1500
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 20,
                            "method": "CreateSessionObject",
                            "handle": docHandle,
                            "params": [{
                                "qInfo": { "qType": "q_cats_dia_3p" },
                                "qHyperCubeDef": {
                                    "qDimensions": [
                                        { "qDef": { "qFieldDefs": ["Desc_Grupo"] } },
                                        { "qDef": { "qFieldDefs": ["Desc_Subgrupo"] } }
                                    ],
                                    "qMeasures": [
                                        { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-08'}>} [Receita Líquida])", "qLabel": "Ago_26" } },
                                        { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-07'}>} [Receita Líquida])", "qLabel": "Jul_26" } },
                                        { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2025-08'}>} [Receita Líquida])", "qLabel": "Ago_25" } }
                                    ],
                                    "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 1500, "qWidth": 5 }],
                                    "qSuppressZero": true, "qSuppressMissing": true
                                }
                            }]
                        }));
                    } else if (msg.id === 20 && msg.result) {
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 21,
                            "method": "GetLayout",
                            "handle": msg.result.qReturn.qHandle,
                            "params": []
                        }));
                    } else if (msg.id === 21 && msg.result) {
                        const hc = msg.result.qLayout.qHyperCube;
                        results.categorias = (hc.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));
                        
                        // 3. Hierarquia (Grupo + Subgrupo + Linha) x Canal (3 períodos)
                        // Width 6 -> Height 1500
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 30,
                            "method": "CreateSessionObject",
                            "handle": docHandle,
                            "params": [{
                                "qInfo": { "qType": "q_hier_canal_3p" },
                                "qHyperCubeDef": {
                                    "qDimensions": [
                                        { "qDef": { "qFieldDefs": ["Desc_Grupo"] } },
                                        { "qDef": { "qFieldDefs": ["Desc_Subgrupo"] } },
                                        { "qDef": { "qFieldDefs": ["Desc_Linha"] } },
                                        { "qDef": { "qFieldDefs": ["Canal"] } }
                                    ],
                                    "qMeasures": [
                                        { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-08'}>} [Receita Líquida])", "qLabel": "Ago_26" } },
                                        { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2026-07'}>} [Receita Líquida])", "qLabel": "Jul_26" } },
                                        { "qDef": { "qDef": "Sum({1<[Ano-Mes]={'2025-08'}>} [Receita Líquida])", "qLabel": "Ago_25" } }
                                    ],
                                    "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 1400, "qWidth": 7 }],
                                    "qSuppressZero": true, "qSuppressMissing": true
                                }
                            }]
                        }));
                    } else if (msg.id === 30 && msg.result) {
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 31,
                            "method": "GetLayout",
                            "handle": msg.result.qReturn.qHandle,
                            "params": []
                        }));
                    } else if (msg.id === 31 && msg.result) {
                        const hc = msg.result.qLayout.qHyperCube;
                        results.hier_canal = (hc.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));
                        
                        ws.close();
                        resolve(results);
                    }
                };
                
                ws.onerror = () => resolve({ error: 'ws error' });
                setTimeout(() => resolve({ error: 'timeout', results }), 35000);
            });
        }'''
        
        raw_res = await page.evaluate(queries_js)
        await browser.close()
        
        print(f"  ✅ Extração no Qlik Engine concluída em {time.time() - t0:.2f}s!")
        return raw_res

def process_and_save_agosto_models(raw_res):
    print("\n  3/4 Processando matrizes e calculando modelos de dados...")
    t1 = time.time()
    
    canais_raw = raw_res.get('canais_dia', [])
    cats_raw = raw_res.get('categorias', [])
    hier_raw = raw_res.get('hier_canal', [])
    
    print(f"  Registros obtidos -> Canais: {len(canais_raw)}, Categorias: {len(cats_raw)}, Hierarquia: {len(hier_raw)}")
    
    if not canais_raw:
        print("  ❌ Erro: dados de Canais vazios.")
        return

    # 1. CANAIS SUMMARY
    df_c = pd.DataFrame(canais_raw, columns=['canal', 'dia', 'ago_26', 'jul_26', 'ago_25'])
    df_c['canal'] = df_c['canal'].apply(clean_str)
    df_c['dia'] = pd.to_numeric(df_c['dia'], errors='coerce').fillna(1).astype(int)
    df_c['ago_26'] = pd.to_numeric(df_c['ago_26'], errors='coerce').fillna(0.0)
    df_c['jul_26'] = pd.to_numeric(df_c['jul_26'], errors='coerce').fillna(0.0)
    df_c['ago_25'] = pd.to_numeric(df_c['ago_25'], errors='coerce').fillna(0.0)
    df_c['grupo'] = df_c['canal'].apply(get_channel_group)
    
    d_max = int(df_c[df_c['ago_26'] > 0]['dia'].max()) if len(df_c[df_c['ago_26'] > 0]) > 0 else 19
    print(f"  📅 Período identificado: 01 a {d_max:02d}/08/2026 (D-1)")
    
    canais_list = []
    tot_cur = float(df_c[df_c['dia'] <= d_max]['ago_26'].sum())
    tot_mo = float(df_c[df_c['dia'] <= d_max]['jul_26'].sum())
    tot_yr = float(df_c[df_c['dia'] <= d_max]['ago_25'].sum())
    
    for canal_name, c_df in df_c.groupby('canal'):
        c_grp = get_channel_group(canal_name)
        d_cur = [0.0] * 31
        d_mo = [0.0] * 31
        d_yr = [0.0] * 31
        
        for _, r in c_df.iterrows():
            d_idx = int(r['dia']) - 1
            if 0 <= d_idx < 31:
                d_cur[d_idx] += float(r['ago_26'])
                d_mo[d_idx] += float(r['jul_26'])
                d_yr[d_idx] += float(r['ago_25'])
                
        v_cur = round(sum(d_cur[:d_max]), 2)
        v_mo = round(sum(d_mo[:d_max]), 2)
        v_yr = round(sum(d_yr[:d_max]), 2)
        
        m_pct, m_rs = calc_growth(v_cur, v_mo)
        y_pct, y_rs = calc_growth(v_cur, v_yr)
        
        sh_cur = round((v_cur / tot_cur * 100.0) if tot_cur > 0 else 0.0, 2)
        sh_mo = round((v_mo / tot_mo * 100.0) if tot_mo > 0 else 0.0, 2)
        sh_yr = round((v_yr / tot_yr * 100.0) if tot_yr > 0 else 0.0, 2)
        
        canais_list.append({
            'canal': canal_name,
            'grupo': c_grp,
            'venda_jul_26': v_cur,
            'venda_jun_26': v_mo,
            'venda_jul_25': v_yr,
            'mom_pct': m_pct, 'mom_rs': m_rs,
            'yoy_pct': y_pct, 'yoy_rs': y_rs,
            'part_jul_26': sh_cur,
            'part_jun_26': sh_mo,
            'part_jul_25': sh_yr,
            'var_pp': round(sh_cur - sh_yr, 2),
            'd25': [round(x, 2) for x in d_yr],
            'd26_06': [round(x, 2) for x in d_mo],
            'd26_07': [round(x, 2) for x in d_cur]
        })
        
    canais_list.sort(key=lambda x: x['venda_jul_26'], reverse=True)
    
    # 2. CATEGORIAS SUMMARY
    cats_list = []
    if cats_raw:
        df_cat = pd.DataFrame(cats_raw, columns=['grupo', 'subgrupo', 'ago_26', 'jul_26', 'ago_25'])
        df_cat['grupo'] = df_cat['grupo'].apply(clean_str)
        df_cat['subgrupo'] = df_cat['subgrupo'].apply(clean_str)
        df_cat['ago_26'] = pd.to_numeric(df_cat['ago_26'], errors='coerce').fillna(0.0)
        df_cat['jul_26'] = pd.to_numeric(df_cat['jul_26'], errors='coerce').fillna(0.0)
        df_cat['ago_25'] = pd.to_numeric(df_cat['ago_25'], errors='coerce').fillna(0.0)
        
        for (g, sg), cat_df in df_cat.groupby(['grupo', 'subgrupo']):
            v_cur = round(float(cat_df['ago_26'].sum()), 2)
            v_mo = round(float(cat_df['jul_26'].sum()), 2)
            v_yr = round(float(cat_df['ago_25'].sum()), 2)
            
            m_pct, m_rs = calc_growth(v_cur, v_mo)
            y_pct, y_rs = calc_growth(v_cur, v_yr)
            
            sh_cur = round((v_cur / tot_cur * 100.0) if tot_cur > 0 else 0.0, 2)
            sh_mo = round((v_mo / tot_mo * 100.0) if tot_mo > 0 else 0.0, 2)
            sh_yr = round((v_yr / tot_yr * 100.0) if tot_yr > 0 else 0.0, 2)
            
            cats_list.append({
                'diretor': '',
                'distrital': '',
                'grupo': g,
                'subgrupo': sg,
                'venda_jul_26': v_cur,
                'venda_jun_26': v_mo,
                'venda_jul_25': v_yr,
                'venda_digital_jul_26': 0.0,
                'venda_digital_jun_26': 0.0,
                'venda_digital_jul_25': 0.0,
                'venda_dt_jul_26': 0.0,
                'venda_dt_jun_26': 0.0,
                'venda_dt_jul_25': 0.0,
                'mom_pct': m_pct, 'mom_rs': m_rs,
                'yoy_pct': y_pct, 'yoy_rs': y_rs,
                'part_jul_26': sh_cur,
                'part_jun_26': sh_mo,
                'part_jul_25': sh_yr,
                'var_pp': round(sh_cur - sh_yr, 2),
                'd25': [0.0]*31, 'd26_06': [0.0]*31, 'd26_07': [0.0]*31,
                'dig_d25': [0.0]*31, 'dig_d26_06': [0.0]*31, 'dig_d26_07': [0.0]*31,
                'dt_d25': [0.0]*31, 'dt_d26_06': [0.0]*31, 'dt_d26_07': [0.0]*31
            })
            
        cats_list.sort(key=lambda x: x['venda_jul_26'], reverse=True)
        
    # 3. CANAIS BY HIERARQUIA
    canais_hier_list = []
    if hier_raw:
        df_h = pd.DataFrame(hier_raw, columns=['grupo', 'subgrupo', 'linha', 'canal', 'ago_26', 'jul_26', 'ago_25'])
        df_h['grupo'] = df_h['grupo'].apply(clean_str)
        df_h['subgrupo'] = df_h['subgrupo'].apply(clean_str)
        df_h['linha'] = df_h['linha'].apply(clean_str)
        df_h['canal'] = df_h['canal'].apply(clean_str)
        df_h['ago_26'] = pd.to_numeric(df_h['ago_26'], errors='coerce').fillna(0.0)
        df_h['jul_26'] = pd.to_numeric(df_h['jul_26'], errors='coerce').fillna(0.0)
        df_h['ago_25'] = pd.to_numeric(df_h['ago_25'], errors='coerce').fillna(0.0)
        df_h['canal_grupo'] = df_h['canal'].apply(get_channel_group)
        
        for (g, sg, l, c), h_df in df_h.groupby(['grupo', 'subgrupo', 'linha', 'canal']):
            v_cur = float(h_df['ago_26'].sum())
            v_mo = float(h_df['jul_26'].sum())
            v_yr = float(h_df['ago_25'].sum())
            c_grp = get_channel_group(c)
            
            canais_hier_list.append({
                'grupo': g, 'subgrupo': sg, 'linha': l,
                'canal': c, 'canal_grupo': c_grp,
                'v26': round(v_cur, 2),
                'v26_06': round(v_mo, 2),
                'v25': round(v_yr, 2),
                'd25': [0.0]*31, 'd26_06': [0.0]*31, 'd26_07': [0.0]*31
            })
            
    # 4. HIERARQUIA DETALHADA
    hier_detalhada_list = []
    if hier_raw:
        df_hd = pd.DataFrame(hier_raw, columns=['grupo', 'subgrupo', 'linha', 'canal', 'ago_26', 'jul_26', 'ago_25'])
        df_hd['grupo'] = df_hd['grupo'].apply(clean_str)
        df_hd['subgrupo'] = df_hd['subgrupo'].apply(clean_str)
        df_hd['linha'] = df_hd['linha'].apply(clean_str)
        df_hd['canal'] = df_hd['canal'].apply(clean_str)
        df_hd['ago_26'] = pd.to_numeric(df_hd['ago_26'], errors='coerce').fillna(0.0)
        df_hd['jul_26'] = pd.to_numeric(df_hd['jul_26'], errors='coerce').fillna(0.0)
        df_hd['ago_25'] = pd.to_numeric(df_hd['ago_25'], errors='coerce').fillna(0.0)
        df_hd['canal_grupo'] = df_hd['canal'].apply(get_channel_group)
        
        for (g, sg, l), h_df in df_hd.groupby(['grupo', 'subgrupo', 'linha']):
            v_cur = float(h_df['ago_26'].sum())
            v_mo = float(h_df['jul_26'].sum())
            v_yr = float(h_df['ago_25'].sum())
            
            v_dig_cur = float(h_df[h_df['canal_grupo'] == 'digital']['ago_26'].sum())
            v_dig_mo = float(h_df[h_df['canal_grupo'] == 'digital']['jul_26'].sum())
            v_dig_yr = float(h_df[h_df['canal_grupo'] == 'digital']['ago_25'].sum())
            
            v_dt_cur = float(h_df[h_df['canal_grupo'].isin(['digital', 'tele'])]['ago_26'].sum())
            v_dt_mo = float(h_df[h_df['canal_grupo'].isin(['digital', 'tele'])]['jul_26'].sum())
            v_dt_yr = float(h_df[h_df['canal_grupo'].isin(['digital', 'tele'])]['ago_25'].sum())
            
            m_pct, m_rs = calc_growth(v_cur, v_mo)
            y_pct, y_rs = calc_growth(v_cur, v_yr)
            
            hier_detalhada_list.append({
                'grupo': g, 'subgrupo': sg, 'linha': l,
                'venda_jul_26': round(v_cur, 2),
                'venda_jun_26': round(v_mo, 2),
                'venda_jul_25': round(v_yr, 2),
                'venda_digital_jul_26': round(v_dig_cur, 2),
                'venda_digital_jun_26': round(v_dig_mo, 2),
                'venda_digital_jul_25': round(v_dig_yr, 2),
                'venda_dt_jul_26': round(v_dt_cur, 2),
                'venda_dt_jun_26': round(v_dt_mo, 2),
                'venda_dt_jul_25': round(v_dt_yr, 2),
                'mom_pct': m_pct, 'mom_rs': m_rs,
                'yoy_pct': y_pct, 'yoy_rs': y_rs,
                'd25': [0.0]*31, 'd26_06': [0.0]*31, 'd26_07': [0.0]*31,
                'dig_d25': [0.0]*31, 'dig_d26_06': [0.0]*31, 'dig_d26_07': [0.0]*31,
                'dt_d25': [0.0]*31, 'dt_d26_06': [0.0]*31, 'dt_d26_07': [0.0]*31
            })
            
        hier_detalhada_list.sort(key=lambda x: x['venda_jul_26'], reverse=True)

    # 5. EXECUTIVE KPIS
    v_dig_tot_cur = sum(c['venda_jul_26'] for c in canais_list if c['grupo'] == 'digital')
    v_dig_tot_mo = sum(c['venda_jun_26'] for c in canais_list if c['grupo'] == 'digital')
    v_dig_tot_yr = sum(c['venda_jul_25'] for c in canais_list if c['grupo'] == 'digital')
    
    v_dt_tot_cur = sum(c['venda_jul_26'] for c in canais_list if c['grupo'] in ['digital', 'tele'])
    v_dt_tot_mo = sum(c['venda_jun_26'] for c in canais_list if c['grupo'] in ['digital', 'tele'])
    v_dt_tot_yr = sum(c['venda_jul_25'] for c in canais_list if c['grupo'] in ['digital', 'tele'])
    
    kpis = {
        'venda_jul_26': round(tot_cur, 2),
        'venda_jun_26': round(tot_mo, 2),
        'venda_jul_25': round(tot_yr, 2),
        'venda_digital_jul_26': round(v_dig_tot_cur, 2),
        'venda_digital_jun_26': round(v_dig_tot_mo, 2),
        'venda_digital_jul_25': round(v_dig_tot_yr, 2),
        'venda_dt_jul_26': round(v_dt_tot_cur, 2),
        'venda_dt_jun_26': round(v_dt_tot_mo, 2),
        'venda_dt_jul_25': round(v_dt_tot_yr, 2),
        'mom_pct': calc_growth(tot_cur, tot_mo)[0],
        'mom_rs': calc_growth(tot_cur, tot_mo)[1],
        'yoy_pct': calc_growth(tot_cur, tot_yr)[0],
        'yoy_rs': calc_growth(tot_cur, tot_yr)[1],
        'd_max': d_max
    }
    
    # 6. FILTROS
    filtro_hier = {}
    for r in canais_hier_list:
        g = r['grupo']
        sg = r['subgrupo']
        l = r['linha']
        if g not in filtro_hier: filtro_hier[g] = {}
        if sg not in filtro_hier[g]: filtro_hier[g][sg] = []
        if l not in filtro_hier[g][sg]: filtro_hier[g][sg].append(l)
        
    filtros_produto = {
        'diretores': sorted(list(set(c.get('diretor','') for c in cats_list if c.get('diretor')))),
        'distritais': sorted(list(set(c.get('distrital','') for c in cats_list if c.get('distrital')))),
        'grupos': sorted(list(filtro_hier.keys()))
    }
    
    # Salvar JSONs em data/agosto/
    with open(os.path.join(AGOSTO_DIR, 'canais_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(canais_list, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(AGOSTO_DIR, 'categorias_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(cats_list, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(AGOSTO_DIR, 'canais_by_hierarquia.json'), 'w', encoding='utf-8') as f:
        json.dump(canais_hier_list, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(AGOSTO_DIR, 'hierarquia_detalhada.json'), 'w', encoding='utf-8') as f:
        json.dump(hier_detalhada_list, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(AGOSTO_DIR, 'filtro_hierarquia.json'), 'w', encoding='utf-8') as f:
        json.dump(filtro_hier, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(AGOSTO_DIR, 'filtros_produto.json'), 'w', encoding='utf-8') as f:
        json.dump(filtros_produto, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(AGOSTO_DIR, 'executive_kpis.json'), 'w', encoding='utf-8') as f:
        json.dump(kpis, f, ensure_ascii=False, indent=2)
        
    print(f"  4/4 Todos os JSONs de Agosto salvos com sucesso em {time.time() - t1:.2f}s!")
    print(f"  📊 Total Agosto D-1 (01 a {d_max}): R$ {tot_cur:,.2f} | YoY: {kpis['yoy_pct']:+.1f}% | MoM: {kpis['mom_pct']:+.1f}%")

def main():
    raw_res = asyncio.run(fetch_all_qlik_cubes())
    if raw_res and not raw_res.get('error'):
        process_and_save_agosto_models(raw_res)
    else:
        print("  ❌ Falha na extração de dados do Qlik Sense.")

if __name__ == '__main__':
    main()
