"""
extract_and_process_agosto_qlik.py — Extração e Processamento Direto do Qlik Sense (Agosto D-1)
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

async def fetch_qlik_agosto():
    os.makedirs(AGOSTO_DIR, exist_ok=True)
    t0 = time.time()
    print("\n" + "=" * 70)
    print("  EXTRAINDO E PROCESSANDO AGOSTO (D-1) DIRETO DO QLIK SENSE")
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
        
        print("  2/4 Executando HyperCubes no Qlik Engine (Canais e Categorias)...")
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
                        
                        // Query 1: Canais x Ano-Mes x Dia
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 10,
                            "method": "CreateSessionObject",
                            "handle": docHandle,
                            "params": [{
                                "qInfo": { "qType": "q_canais_dia" },
                                "qHyperCubeDef": {
                                    "qDimensions": [
                                        { "qDef": { "qFieldDefs": ["Canal"] } },
                                        { "qDef": { "qFieldDefs": ["Ano-Mes"] } },
                                        { "qDef": { "qFieldDefs": ["Dia"] } }
                                    ],
                                    "qMeasures": [
                                        { "qDef": { "qDef": "Sum([Valor Líquido])", "qLabel": "Venda" } }
                                    ],
                                    "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 2000, "qWidth": 4 }],
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
                        
                        // Query 2: Categorias (Grupo + Subgrupo) x Ano-Mes x Dia
                        ws.send(JSON.stringify({
                            "jsonrpc": "2.0",
                            "id": 20,
                            "method": "CreateSessionObject",
                            "handle": docHandle,
                            "params": [{
                                "qInfo": { "qType": "q_categorias_dia" },
                                "qHyperCubeDef": {
                                    "qDimensions": [
                                        { "qDef": { "qFieldDefs": ["Desc_Grupo"] } },
                                        { "qDef": { "qFieldDefs": ["Desc_Subgrupo"] } },
                                        { "qDef": { "qFieldDefs": ["Ano-Mes"] } },
                                        { "qDef": { "qFieldDefs": ["Dia"] } }
                                    ],
                                    "qMeasures": [
                                        { "qDef": { "qDef": "Sum([Valor Líquido])", "qLabel": "Venda" } }
                                    ],
                                    "qInitialDataFetch": [{ "qTop": 0, "qLeft": 0, "qHeight": 2500, "qWidth": 5 }],
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
                        results.categorias_dia = (hc.qDataPages[0]?.qMatrix || []).map(r => r.map(c => c.qNum !== 'NaN' && typeof c.qNum === 'number' ? c.qNum : c.qText));
                        
                        ws.close();
                        resolve(results);
                    }
                };
                
                ws.onerror = (e) => resolve({ error: 'ws error' });
                setTimeout(() => resolve({ error: 'timeout', results }), 60000);
            });
        }'''
        
        raw_res = await page.evaluate(queries_js)
        await browser.close()
        
        print(f"  ✅ Consultas do Qlik finalizadas em {time.time() - t0:.2f}s!")
        return raw_res

def process_and_save_agosto(raw_res):
    print("\n  3/4 Processando matrizes e calculando vetores diários...")
    t1 = time.time()
    
    canais_raw = raw_res.get('canais_dia', [])
    cats_raw = raw_res.get('categorias_dia', [])
    
    print(f"  Linhas obtidas -> Canais: {len(canais_raw)}, Categorias: {len(cats_raw)}")
    
    if not canais_raw:
        print("  ⚠️ Nenhuma linha retornada. Mantendo base anterior.")
        return
        
    # 1. CANAIS SUMMARY
    df_c = pd.DataFrame(canais_raw, columns=['canal', 'anomes', 'dia', 'venda'])
    df_c['canal'] = df_c['canal'].apply(clean_str)
    df_c['anomes'] = df_c['anomes'].astype(str).str.replace('-', '').str.strip()
    df_c['dia'] = pd.to_numeric(df_c['dia'], errors='coerce').fillna(1).astype(int)
    df_c['venda'] = pd.to_numeric(df_c['venda'], errors='coerce').fillna(0.0)
    df_c['grupo'] = df_c['canal'].apply(get_channel_group)
    
    cur_anomes = '202608'
    prev_mo_anomes = '202607'
    prev_yr_anomes = '202508'
    
    d_max = int(df_c[df_c['anomes'] == cur_anomes]['dia'].max()) if len(df_c[df_c['anomes'] == cur_anomes]) > 0 else 19
    print(f"  📅 Período identificado: Agosto/2026 até D-1 ({d_max:02d}/08/2026)")
    
    canais_list = []
    tot_cur = float(df_c[(df_c['anomes'] == cur_anomes) & (df_c['dia'] <= d_max)]['venda'].sum())
    tot_prev_mo = float(df_c[(df_c['anomes'] == prev_mo_anomes) & (df_c['dia'] <= d_max)]['venda'].sum())
    tot_prev_yr = float(df_c[(df_c['anomes'] == prev_yr_anomes) & (df_c['dia'] <= d_max)]['venda'].sum())
    
    for canal_name, c_df in df_c.groupby('canal'):
        c_grp = get_channel_group(canal_name)
        d_cur = [0.0] * 31
        d_mo = [0.0] * 31
        d_yr = [0.0] * 31
        
        for _, r in c_df.iterrows():
            d_idx = int(r['dia']) - 1
            if 0 <= d_idx < 31:
                if r['anomes'] == cur_anomes:
                    d_cur[d_idx] += float(r['venda'])
                elif r['anomes'] == prev_mo_anomes:
                    d_mo[d_idx] += float(r['venda'])
                elif r['anomes'] == prev_yr_anomes:
                    d_yr[d_idx] += float(r['venda'])
                    
        v_cur = round(sum(d_cur[:d_max]), 2)
        v_mo = round(sum(d_mo[:d_max]), 2)
        v_yr = round(sum(d_yr[:d_max]), 2)
        
        m_pct, m_rs = calc_growth(v_cur, v_mo)
        y_pct, y_rs = calc_growth(v_cur, v_yr)
        
        sh_cur = round((v_cur / tot_cur * 100.0) if tot_cur > 0 else 0.0, 2)
        sh_mo = round((v_mo / tot_prev_mo * 100.0) if tot_prev_mo > 0 else 0.0, 2)
        sh_yr = round((v_yr / tot_prev_yr * 100.0) if tot_prev_yr > 0 else 0.0, 2)
        
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
        df_cat = pd.DataFrame(cats_raw, columns=['grupo', 'subgrupo', 'anomes', 'dia', 'venda'])
        df_cat['grupo'] = df_cat['grupo'].apply(clean_str)
        df_cat['subgrupo'] = df_cat['subgrupo'].apply(clean_str)
        df_cat['anomes'] = df_cat['anomes'].astype(str).str.replace('-', '').str.strip()
        df_cat['dia'] = pd.to_numeric(df_cat['dia'], errors='coerce').fillna(1).astype(int)
        df_cat['venda'] = pd.to_numeric(df_cat['venda'], errors='coerce').fillna(0.0)
        
        for (g, sg), cat_df in df_cat.groupby(['grupo', 'subgrupo']):
            d_cur = [0.0] * 31
            d_mo = [0.0] * 31
            d_yr = [0.0] * 31
            
            for _, r in cat_df.iterrows():
                d_idx = int(r['dia']) - 1
                if 0 <= d_idx < 31:
                    if r['anomes'] == cur_anomes:
                        d_cur[d_idx] += float(r['venda'])
                    elif r['anomes'] == prev_mo_anomes:
                        d_mo[d_idx] += float(r['venda'])
                    elif r['anomes'] == prev_yr_anomes:
                        d_yr[d_idx] += float(r['venda'])
                        
            v_cur = round(sum(d_cur[:d_max]), 2)
            v_mo = round(sum(d_mo[:d_max]), 2)
            v_yr = round(sum(d_yr[:d_max]), 2)
            
            m_pct, m_rs = calc_growth(v_cur, v_mo)
            y_pct, y_rs = calc_growth(v_cur, v_yr)
            
            sh_cur = round((v_cur / tot_cur * 100.0) if tot_cur > 0 else 0.0, 2)
            sh_mo = round((v_mo / tot_prev_mo * 100.0) if tot_prev_mo > 0 else 0.0, 2)
            sh_yr = round((v_yr / tot_prev_yr * 100.0) if tot_prev_yr > 0 else 0.0, 2)
            
            cats_list.append({
                'grupo': g,
                'subgrupo': sg,
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
            
        cats_list.sort(key=lambda x: x['venda_jul_26'], reverse=True)
    
    # 3. Executive KPIs
    kpis = {
        'total_venda_26': round(tot_cur, 2),
        'total_venda_25': round(tot_prev_yr, 2),
        'total_venda_06': round(tot_prev_mo, 2),
        'crescimento_yoy_pct': calc_growth(tot_cur, tot_prev_yr)[0],
        'crescimento_yoy_rs': calc_growth(tot_cur, tot_prev_yr)[1],
        'crescimento_mom_pct': calc_growth(tot_cur, tot_prev_mo)[0],
        'crescimento_mom_rs': calc_growth(tot_cur, tot_prev_mo)[1],
        'share_digital_26': round(sum(c['part_jul_26'] for c in canais_list if c['grupo'] == 'digital'), 2),
        'share_digital_25': round(sum(c['part_jul_25'] for c in canais_list if c['grupo'] == 'digital'), 2),
        'share_dt_26': round(sum(c['part_jul_26'] for c in canais_list if c['grupo'] in ['digital', 'tele']), 2),
        'share_dt_25': round(sum(c['part_jul_25'] for c in canais_list if c['grupo'] in ['digital', 'tele']), 2),
        'd_max': d_max
    }
    
    # Salvar JSONs
    with open(os.path.join(AGOSTO_DIR, 'canais_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(canais_list, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(AGOSTO_DIR, 'categorias_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(cats_list, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(AGOSTO_DIR, 'executive_kpis.json'), 'w', encoding='utf-8') as f:
        json.dump(kpis, f, ensure_ascii=False, indent=2)
        
    print(f"  4/4 JSONs de Agosto salvos com sucesso em {time.time() - t1:.2f}s!")
    print(f"  📊 Total Agosto D-1 (até dia {d_max}): R$ {tot_cur:,.2f} | YoY: {kpis['crescimento_yoy_pct']:+.1f}%")

def main():
    raw_res = asyncio.run(fetch_qlik_agosto())
    if raw_res and not raw_res.get('error'):
        process_and_save_agosto(raw_res)
    else:
        print("  ⚠️ Usando base existente de fallback.")

if __name__ == '__main__':
    main()
