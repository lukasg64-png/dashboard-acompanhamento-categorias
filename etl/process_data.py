"""
process_data.py — Processa dados de base_dados_daily.parquet e gera JSONs otimizados com precisão EXATA de centavos.
"""
import os, sys, time, json
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DAILY_PARQUET = os.path.join(DATA_DIR, 'base_dados_daily.parquet')

def clean_str(val):
    if pd.isna(val) or val is None: return ""
    return str(val).replace('\xa0', ' ').replace('\t', ' ').strip()

def calc_growth(cur, prev):
    diff = cur - prev
    pct = (diff / prev * 100.0) if prev > 0 else 0.0
    return round(pct, 2), round(diff, 2)

def get_channel_group(canal_name):
    c = str(canal_name).strip().upper()
    if c in ['APP', 'E_COMMERCE', 'E-COMMERCE', 'IFOOD', 'RAPPI', 'SITE']:
        return 'digital'
    elif c in ['APP TELE ENTREGA', 'SITE TELE ENTREGA', 'TELE ENCAMINHADA LOJAS', 'TELE VIZINHANÇA', 'TELE VIZINHANÇAS', 'VENDA TELE ENTREGA', 'VENDA TELE ENTREGA CENTRAL']:
        return 'tele'
    else:
        return 'loja'

def main():
    t0 = time.time()
    print("=" * 70)
    print("GERANDO JSONS COM PRECISÃO DE CENTAVOS E SOMATÓRIO EXATO DA BASE PARQUET")
    print("=" * 70)

    if not os.path.exists(DAILY_PARQUET):
        print(f"[ERRO] Parquet não encontrado: {DAILY_PARQUET}")
        sys.exit(1)

    df = pd.read_parquet(DAILY_PARQUET)
    print(f"[OK] Parquet diário carregado em {time.time() - t0:.2f}s! Shape: {df.shape}")

    date_cols_jul_25 = [c for c in df.columns if c.endswith('/07/2025')]
    date_cols_jun_26 = [c for c in df.columns if c.endswith('/06/2026')]
    date_cols_jul_26 = [c for c in df.columns if c.endswith('/07/2026')]

    date_cols_jul_25.sort(key=lambda x: int(x.split('/')[0]))
    date_cols_jun_26.sort(key=lambda x: int(x.split('/')[0]))
    date_cols_jul_26.sort(key=lambda x: int(x.split('/')[0]))

    for col in ['diretor', 'distrital', 'grupo', 'subgrupo', 'linha', 'laboratorio', 'canal']:
        df[col] = df[col].apply(clean_str)

    df['canal_grupo'] = df['canal'].apply(get_channel_group)
    df['is_digital'] = df['canal_grupo'] == 'digital'
    df['is_dt'] = (df['canal_grupo'] == 'digital') | (df['canal_grupo'] == 'tele')

    df['venda_jul_25'] = df[date_cols_jul_25].sum(axis=1)
    df['venda_jun_26'] = df[date_cols_jun_26].sum(axis=1)
    df['venda_jul_26'] = df[date_cols_jul_26].sum(axis=1)

    tot_jul_26 = round(float(df['venda_jul_26'].sum()), 2)
    tot_jun_26 = round(float(df['venda_jun_26'].sum()), 2)
    tot_jul_25 = round(float(df['venda_jul_25'].sum()), 2)

    agg_dates = {c: 'sum' for c in date_cols_jul_25 + date_cols_jun_26 + date_cols_jul_26}

    # 1. CANAIS SUMMARY
    print("Processing canais_summary.json...")
    grp_canal = df.groupby(['canal', 'canal_grupo'], as_index=False).agg(agg_dates)

    canais_detalhad_list = []
    for _, r in grp_canal.iterrows():
        c_name = r['canal']
        c_grp = r['canal_grupo']
        d25 = [round(float(r[c]), 2) for c in date_cols_jul_25]
        d26_06 = [round(float(r[c]), 2) for c in date_cols_jun_26]
        d26_07 = [round(float(r[c]), 2) for c in date_cols_jul_26]

        v26 = round(float(r[date_cols_jul_26].sum()), 2)
        v26_06 = round(float(r[date_cols_jun_26].sum()), 2)
        v25 = round(float(r[date_cols_jul_25].sum()), 2)

        m_pct, m_rs = calc_growth(v26, v26_06)
        y_pct, y_rs = calc_growth(v26, v25)

        sh_26 = round((v26 / tot_jul_26 * 100.0) if tot_jul_26 > 0 else 0.0, 2)
        sh_26_06 = round((v26_06 / tot_jun_26 * 100.0) if tot_jun_26 > 0 else 0.0, 2)
        sh_25 = round((v25 / tot_jul_25 * 100.0) if tot_jul_25 > 0 else 0.0, 2)
        var_pp = round(sh_26 - sh_25, 2)

        canais_detalhad_list.append({
            'canal': c_name, 'grupo': c_grp,
            'venda_jul_26': v26, 'venda_jun_26': v26_06, 'venda_jul_25': v25,
            'mom_pct': m_pct, 'mom_rs': m_rs, 'yoy_pct': y_pct, 'yoy_rs': y_rs,
            'part_jul_26': sh_26, 'part_jun_26': sh_26_06, 'part_jul_25': sh_25, 'var_pp': var_pp,
            'd25': d25, 'd26_06': d26_06, 'd26_07': d26_07
        })

    canais_detalhad_list.sort(key=lambda x: x['venda_jul_26'], reverse=True)
    with open(os.path.join(DATA_DIR, 'canais_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(canais_detalhad_list, f, ensure_ascii=False, indent=2)

    # 2. CANAIS BY HIERARQUIA (grupo, subgrupo, linha, canal)
    print("Processing canais_by_hierarquia.json...")
    grp_c_hier = df.groupby(['grupo', 'subgrupo', 'linha', 'canal', 'canal_grupo'], as_index=False).agg(agg_dates)

    canais_hier_list = []
    for _, r in grp_c_hier.iterrows():
        d25 = [round(float(r[c]), 2) for c in date_cols_jul_25]
        d26_06 = [round(float(r[c]), 2) for c in date_cols_jun_26]
        d26_07 = [round(float(r[c]), 2) for c in date_cols_jul_26]

        v26 = round(float(r[date_cols_jul_26].sum()), 2)
        v26_06 = round(float(r[date_cols_jun_26].sum()), 2)
        v25 = round(float(r[date_cols_jul_25].sum()), 2)

        canais_hier_list.append({
            'diretor': '', 'distrital': '',
            'grupo': r['grupo'], 'subgrupo': r['subgrupo'], 'linha': r['linha'],
            'canal': r['canal'], 'canal_grupo': r['canal_grupo'],
            'v26': v26, 'v26_06': v26_06, 'v25': v25,
            'd25': d25, 'd26_06': d26_06, 'd26_07': d26_07
        })

    with open(os.path.join(DATA_DIR, 'canais_by_hierarquia.json'), 'w', encoding='utf-8') as f:
        json.dump(canais_hier_list, f, ensure_ascii=False, indent=2)

    # 3. CATEGORIAS SUMMARY
    print("Processing categorias_summary.json...")
    grp_cat = df.groupby(['diretor', 'distrital', 'grupo'], as_index=False).agg(agg_dates)
    df_dig = df[df['is_digital']].groupby(['diretor', 'distrital', 'grupo'], as_index=False).agg(agg_dates)
    df_dt = df[df['is_dt']].groupby(['diretor', 'distrital', 'grupo'], as_index=False).agg(agg_dates)

    dig_map = { (r['diretor'], r['distrital'], r['grupo']): r for _, r in df_dig.iterrows() }
    dt_map = { (r['diretor'], r['distrital'], r['grupo']): r for _, r in df_dt.iterrows() }

    cat_records = []
    for _, r in grp_cat.iterrows():
        k = (r['diretor'], r['distrital'], r['grupo'])
        d25 = [round(float(r[c]), 2) for c in date_cols_jul_25]
        d26_06 = [round(float(r[c]), 2) for c in date_cols_jun_26]
        d26_07 = [round(float(r[c]), 2) for c in date_cols_jul_26]

        v26 = round(float(r[date_cols_jul_26].sum()), 2)
        v26_06 = round(float(r[date_cols_jun_26].sum()), 2)
        v25 = round(float(r[date_cols_jul_25].sum()), 2)
        m_pct, m_rs = calc_growth(v26, v26_06)
        y_pct, y_rs = calc_growth(v26, v25)

        r_dig = dig_map.get(k)
        dig_d25 = [round(float(r_dig[c]), 2) for c in date_cols_jul_25] if r_dig is not None else [0.0]*len(date_cols_jul_25)
        dig_d26_06 = [round(float(r_dig[c]), 2) for c in date_cols_jun_26] if r_dig is not None else [0.0]*len(date_cols_jun_26)
        dig_d26_07 = [round(float(r_dig[c]), 2) for c in date_cols_jul_26] if r_dig is not None else [0.0]*len(date_cols_jul_26)

        v_dig26 = round(float(r_dig[date_cols_jul_26].sum()), 2) if r_dig is not None else 0.0
        v_dig26_06 = round(float(r_dig[date_cols_jun_26].sum()), 2) if r_dig is not None else 0.0
        v_dig25 = round(float(r_dig[date_cols_jul_25].sum()), 2) if r_dig is not None else 0.0

        r_dt = dt_map.get(k)
        dt_d25 = [round(float(r_dt[c]), 2) for c in date_cols_jul_25] if r_dt is not None else [0.0]*len(date_cols_jul_25)
        dt_d26_06 = [round(float(r_dt[c]), 2) for c in date_cols_jun_26] if r_dt is not None else [0.0]*len(date_cols_jun_26)
        dt_d26_07 = [round(float(r_dt[c]), 2) for c in date_cols_jul_26] if r_dt is not None else [0.0]*len(date_cols_jul_26)

        v_dt26 = round(float(r_dt[date_cols_jul_26].sum()), 2) if r_dt is not None else 0.0
        v_dt26_06 = round(float(r_dt[date_cols_jun_26].sum()), 2) if r_dt is not None else 0.0
        v_dt25 = round(float(r_dt[date_cols_jul_25].sum()), 2) if r_dt is not None else 0.0

        cat_records.append({
            'diretor': r['diretor'], 'distrital': r['distrital'], 'grupo': r['grupo'],
            'venda_jul_26': v26, 'venda_jun_26': v26_06, 'venda_jul_25': v25,
            'venda_digital_jul_26': v_dig26, 'venda_digital_jun_26': v_dig26_06, 'venda_digital_jul_25': v_dig25,
            'venda_dt_jul_26': v_dt26, 'venda_dt_jun_26': v_dt26_06, 'venda_dt_jul_25': v_dt25,
            'd25': d25, 'd26_06': d26_06, 'd26_07': d26_07,
            'dig_d25': dig_d25, 'dig_d26_06': dig_d26_06, 'dig_d26_07': dig_d26_07,
            'dt_d25': dt_d25, 'dt_d26_06': dt_d26_06, 'dt_d26_07': dt_d26_07,
            'mom_pct': m_pct, 'mom_rs': m_rs, 'yoy_pct': y_pct, 'yoy_rs': y_rs
        })

    with open(os.path.join(DATA_DIR, 'categorias_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(cat_records, f, ensure_ascii=False, indent=2)

    # 4. HIERARQUIA DETALHADA
    print("Processing hierarquia_detalhada.json...")

    grp_hier = df.groupby(['grupo', 'subgrupo', 'linha', 'laboratorio'], as_index=False).agg(agg_dates)
    df_hier_dig = df[df['is_digital']].groupby(['grupo', 'subgrupo', 'linha', 'laboratorio'], as_index=False).agg(agg_dates)
    df_hier_dt = df[df['is_dt']].groupby(['grupo', 'subgrupo', 'linha', 'laboratorio'], as_index=False).agg(agg_dates)

    h_dig_map = { (r['grupo'], r['subgrupo'], r['linha'], r['laboratorio']): r for _, r in df_hier_dig.iterrows() }
    h_dt_map = { (r['grupo'], r['subgrupo'], r['linha'], r['laboratorio']): r for _, r in df_hier_dt.iterrows() }

    hier_records = []
    for _, r in grp_hier.iterrows():
        hk = (r['grupo'], r['subgrupo'], r['linha'], r['laboratorio'])
        d25 = [round(float(r[c]), 2) for c in date_cols_jul_25]
        d26_06 = [round(float(r[c]), 2) for c in date_cols_jun_26]
        d26_07 = [round(float(r[c]), 2) for c in date_cols_jul_26]

        v26 = round(float(r[date_cols_jul_26].sum()), 2)
        v26_06 = round(float(r[date_cols_jun_26].sum()), 2)
        v25 = round(float(r[date_cols_jul_25].sum()), 2)
        m_pct, m_rs = calc_growth(v26, v26_06)
        y_pct, y_rs = calc_growth(v26, v25)

        r_dig = h_dig_map.get(hk)
        dig_d26_07 = [round(float(r_dig[c]), 2) for c in date_cols_jul_26] if r_dig is not None else [0.0]*len(date_cols_jul_26)
        dig_d26_06 = [round(float(r_dig[c]), 2) for c in date_cols_jun_26] if r_dig is not None else [0.0]*len(date_cols_jun_26)
        dig_d25 = [round(float(r_dig[c]), 2) for c in date_cols_jul_25] if r_dig is not None else [0.0]*len(date_cols_jul_25)

        v_dig26 = round(float(r_dig[date_cols_jul_26].sum()), 2) if r_dig is not None else 0.0
        v_dig26_06 = round(float(r_dig[date_cols_jun_26].sum()), 2) if r_dig is not None else 0.0
        v_dig25 = round(float(r_dig[date_cols_jul_25].sum()), 2) if r_dig is not None else 0.0

        r_dt = h_dt_map.get(hk)
        dt_d26_07 = [round(float(r_dt[c]), 2) for c in date_cols_jul_26] if r_dt is not None else [0.0]*len(date_cols_jul_26)
        dt_d26_06 = [round(float(r_dt[c]), 2) for c in date_cols_jun_26] if r_dt is not None else [0.0]*len(date_cols_jun_26)
        dt_d25 = [round(float(r_dt[c]), 2) for c in date_cols_jul_25] if r_dt is not None else [0.0]*len(date_cols_jul_25)

        v_dt26 = round(float(r_dt[date_cols_jul_26].sum()), 2) if r_dt is not None else 0.0
        v_dt26_06 = round(float(r_dt[date_cols_jun_26].sum()), 2) if r_dt is not None else 0.0
        v_dt25 = round(float(r_dt[date_cols_jul_25].sum()), 2) if r_dt is not None else 0.0

        hier_records.append({
            'diretor': '', 'distrital': '', 'grupo': r['grupo'],
            'subgrupo': r['subgrupo'], 'linha': r['linha'], 'laboratorio': r['laboratorio'],
            'venda_jul_26': v26, 'venda_jun_26': v26_06, 'venda_jul_25': v25,
            'venda_digital_jul_26': v_dig26, 'venda_digital_jun_26': v_dig26_06, 'venda_digital_jul_25': v_dig25,
            'venda_dt_jul_26': v_dt26, 'venda_dt_jun_26': v_dt26_06, 'venda_dt_jul_25': v_dt25,
            'd25': d25, 'd26_06': d26_06, 'd26_07': d26_07,
            'dig_d25': dig_d25, 'dig_d26_06': dig_d26_06, 'dig_d26_07': dig_d26_07,
            'dt_d25': dt_d25, 'dt_d26_06': dt_d26_06, 'dt_d26_07': dt_d26_07,
            'mom_pct': m_pct, 'mom_rs': m_rs, 'yoy_pct': y_pct, 'yoy_rs': y_rs
        })

    with open(os.path.join(DATA_DIR, 'hierarquia_detalhada.json'), 'w', encoding='utf-8') as f:
        json.dump(hier_records, f, ensure_ascii=False, indent=2)

    # 5. FILTROS & KPIS
    filtro_hier = {
        'diretores': sorted([x for x in df['diretor'].unique() if x]),
        'distritais': sorted([x for x in df['distrital'].unique() if x]),
        'grupos': sorted([x for x in df['grupo'].unique() if x]),
        'subgrupos': sorted([x for x in df['subgrupo'].unique() if x]),
        'linhas': sorted([x for x in df['linha'].unique() if x]),
        'laboratorios': sorted([x for x in df['laboratorio'].unique() if x])[:200]
    }
    with open(os.path.join(DATA_DIR, 'filtro_hierarquia.json'), 'w', encoding='utf-8') as f:
        json.dump(filtro_hier, f, ensure_ascii=False, indent=2)

    filtros_prod = {
        'grupos': sorted([x for x in df['grupo'].unique() if x]),
        'subgrupos': sorted([x for x in df['subgrupo'].unique() if x]),
        'linhas': sorted([x for x in df['linha'].unique() if x]),
        'laboratorios': sorted([x for x in df['laboratorio'].unique() if x])[:200]
    }
    with open(os.path.join(DATA_DIR, 'filtros_produto.json'), 'w', encoding='utf-8') as f:
        json.dump(filtros_prod, f, ensure_ascii=False, indent=2)

    tot_digital_jul_26 = round(float(df[df['is_digital']]['venda_jul_26'].sum()), 2)
    tot_digital_jun_26 = round(float(df[df['is_digital']]['venda_jun_26'].sum()), 2)
    tot_digital_jul_25 = round(float(df[df['is_digital']]['venda_jul_25'].sum()), 2)

    tot_dt_jul_26 = round(float(df[df['is_dt']]['venda_jul_26'].sum()), 2)
    tot_dt_jun_26 = round(float(df[df['is_dt']]['venda_jun_26'].sum()), 2)
    tot_dt_jul_25 = round(float(df[df['is_dt']]['venda_jul_25'].sum()), 2)

    mom_pct, mom_rs = calc_growth(tot_jul_26, tot_jun_26)
    yoy_pct, yoy_rs = calc_growth(tot_jul_26, tot_jul_25)

    executive_kpis = {
        'venda_jul_26': tot_jul_26, 'venda_jun_26': tot_jun_26, 'venda_jul_25': tot_jul_25,
        'venda_digital_jul_26': tot_digital_jul_26, 'venda_digital_jun_26': tot_digital_jun_26, 'venda_digital_jul_25': tot_digital_jul_25,
        'venda_dt_jul_26': tot_dt_jul_26, 'venda_dt_jun_26': tot_dt_jun_26, 'venda_dt_jul_25': tot_dt_jul_25,
        'mom_pct': mom_pct, 'mom_rs': mom_rs,
        'yoy_pct': yoy_pct, 'yoy_rs': yoy_rs
    }
    with open(os.path.join(DATA_DIR, 'executive_kpis.json'), 'w', encoding='utf-8') as f:
        json.dump(executive_kpis, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] TODOS OS ARQUIVOS JSON GERADOS COM SUCESSO EM {time.time() - t0:.2f}s!")

if __name__ == '__main__':
    main()
