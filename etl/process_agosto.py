"""
process_agosto.py — Processa Base Parcial agosto (layout pivotado: canais x 3 períodos)
e gera JSONs no mesmo formato que o dashboard espera.

Layout da base:
  Cols 0-7: Desc_Grupo, Desc_Subgrupo, Agrupamento, Desc_Linha, Laboratorio, Desc_Produto, Diretor, Distrital
  Col 8: (Canal header -> "Ano-Mes" na row 1)
  Cols 9+: Para cada canal, 3 colunas: 2025-08, 2026-07, 2026-08
"""
import os, sys, time, json, shutil, tempfile
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'agosto')
SRC_FILE = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\Acompanhamento Categorias\Base Parcial agosto de 01 a 17 .xlsx"

def clean_str(val):
    if pd.isna(val) or val is None or str(val).strip() == '-':
        return ""
    return str(val).replace('\xa0', ' ').replace('\t', ' ').strip()

def to_float(val):
    if pd.isna(val) or val is None or str(val).strip() == '-':
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

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

def main():
    t0 = time.time()
    print("=" * 70)
    print("PROCESSANDO BASE PARCIAL AGOSTO")
    print("=" * 70)

    os.makedirs(DATA_DIR, exist_ok=True)

    # Copy to temp
    tmp = os.path.join(tempfile.gettempdir(), 'BASE_AGOSTO_proc.xlsx')
    print(f"Copiando {SRC_FILE} para temp...")
    shutil.copy2(SRC_FILE, tmp)
    print(f"Copiado: {os.path.getsize(tmp)/1e6:.1f} MB")

    # Read with multi-level header
    print("Lendo Excel (header duplo)...")
    df_raw = pd.read_excel(tmp, header=None)
    print(f"Raw shape: {df_raw.shape}")

    # Parse header structure
    # Row 0: canal names (NaN for hierarchy cols, then canal names repeating 3x each)
    # Row 1: column descriptions (Desc_Grupo, ... then Ano-Mes periods: 2025-08, 2026-07, 2026-08)
    # Row 2+: data

    row0 = df_raw.iloc[0].tolist()  # Canal names
    row1 = df_raw.iloc[1].tolist()  # Sub-headers (field names + periods)

    # Build column mapping
    hier_cols = {}  # idx -> field_name
    data_cols = {}  # idx -> (canal, period)

    # Hierarchy columns (0-7)
    for i in range(8):
        field = clean_str(row1[i])
        if field:
            hier_cols[i] = field.lower().replace('desc_', '').replace('laboratorio', 'laboratorio').replace('desc_produto', 'produto')

    # Rename hierarchy fields to match our standard
    field_remap = {
        'grupo': 'grupo',
        'subgrupo': 'subgrupo',
        'agrupamento': 'agrupamento',
        'linha': 'linha',
        'laboratorio': 'laboratorio',
        'produto': 'produto',
        'diretor': 'diretor',
        'distrital': 'distrital'
    }
    for i in hier_cols:
        hier_cols[i] = field_remap.get(hier_cols[i], hier_cols[i])

    print(f"Hierarchy columns: {hier_cols}")

    # Data columns (9+): canal x period
    current_canal = None
    for i in range(9, len(row0)):
        canal_raw = row0[i]
        if pd.notna(canal_raw) and str(canal_raw).strip():
            current_canal = str(canal_raw).strip()
        period = clean_str(row1[i])
        if current_canal and period:
            data_cols[i] = (current_canal, period)

    # Get unique canals and periods
    canals = sorted(set(c for c, p in data_cols.values()))
    periods = sorted(set(p for c, p in data_cols.values()))
    print(f"Canais encontrados: {canals}")
    print(f"Periodos encontrados: {periods}")

    # Map periods to our standard names
    # We expect: 2025-08 (YoY), 2026-07 (MoM), 2026-08 (current)
    period_map = {}
    for p in periods:
        year, month = p.split('-')
        if year == '2025':
            period_map[p] = 'yoy'    # Ago/25
        elif year == '2026' and month == '07':
            period_map[p] = 'mom'    # Jul/26
        elif year == '2026' and month == '08':
            period_map[p] = 'cur'    # Ago/26
        else:
            period_map[p] = p

    print(f"Period mapping: {period_map}")

    # Build tidy dataframe from row 2 onwards
    data_rows = df_raw.iloc[2:].reset_index(drop=True)
    print(f"Data rows: {data_rows.shape[0]}")

    records = []
    for idx, raw_row in data_rows.iterrows():
        # Get hierarchy values
        grupo = clean_str(raw_row.iloc[0])
        subgrupo = clean_str(raw_row.iloc[1])
        agrupamento = clean_str(raw_row.iloc[2])
        linha = clean_str(raw_row.iloc[3])
        laboratorio = clean_str(raw_row.iloc[4])
        produto = clean_str(raw_row.iloc[5])
        diretor = clean_str(raw_row.iloc[6])
        distrital = clean_str(raw_row.iloc[7])

        # For each canal, extract 3 period values
        canal_values = {}
        for col_idx, (canal, period) in data_cols.items():
            p_key = period_map.get(period, period)
            val = to_float(raw_row.iloc[col_idx])
            canal_values[(canal, p_key)] = val

        # Create one row per canal (melted)
        canal_set = set(c for c, p in canal_values.keys())
        for canal in canal_set:
            v_cur = canal_values.get((canal, 'cur'), 0.0)
            v_mom = canal_values.get((canal, 'mom'), 0.0)
            v_yoy = canal_values.get((canal, 'yoy'), 0.0)

            # Skip rows with all zeros
            if v_cur == 0 and v_mom == 0 and v_yoy == 0:
                continue

            records.append({
                'grupo': grupo, 'subgrupo': subgrupo, 'agrupamento': agrupamento,
                'linha': linha, 'laboratorio': laboratorio, 'produto': produto,
                'diretor': diretor, 'distrital': distrital,
                'canal': canal,
                'venda_ago_26': round(v_cur, 2),
                'venda_jul_26': round(v_mom, 2),
                'venda_ago_25': round(v_yoy, 2)
            })

    df = pd.DataFrame(records)
    print(f"\nDataframe tidy: {df.shape}")

    df['canal_grupo'] = df['canal'].apply(get_channel_group)
    df['is_digital'] = df['canal_grupo'] == 'digital'
    df['is_dt'] = (df['canal_grupo'] == 'digital') | (df['canal_grupo'] == 'tele')

    # Totals
    tot_cur = round(float(df['venda_ago_26'].sum()), 2)
    tot_mom = round(float(df['venda_jul_26'].sum()), 2)
    tot_yoy = round(float(df['venda_ago_25'].sum()), 2)

    print(f"\nTotais:")
    print(f"  Ago/26 (D01-D17): R$ {tot_cur:,.2f}")
    print(f"  Jul/26 (D01-D17): R$ {tot_mom:,.2f}")
    print(f"  Ago/25 (D01-D17): R$ {tot_yoy:,.2f}")

    # ============================================================
    # NOTE: We use the SAME field names as julho JSONs so the
    # frontend works without changes. The mapping is:
    #   venda_jul_26 -> current month (Ago/26)
    #   venda_jun_26 -> previous month MoM (Jul/26)
    #   venda_jul_25 -> same month last year YoY (Ago/25)
    # ============================================================

    # 1. CANAIS SUMMARY
    print("\nProcessing canais_summary.json...")
    grp_canal = df.groupby(['canal', 'canal_grupo'], as_index=False).agg({
        'venda_ago_26': 'sum', 'venda_jul_26': 'sum', 'venda_ago_25': 'sum'
    })

    canais_list = []
    for _, r in grp_canal.iterrows():
        v26 = round(float(r['venda_ago_26']), 2)
        v26_06 = round(float(r['venda_jul_26']), 2)
        v25 = round(float(r['venda_ago_25']), 2)

        m_pct, m_rs = calc_growth(v26, v26_06)
        y_pct, y_rs = calc_growth(v26, v25)

        sh_26 = round((v26 / tot_cur * 100.0) if tot_cur > 0 else 0.0, 2)
        sh_26_06 = round((v26_06 / tot_mom * 100.0) if tot_mom > 0 else 0.0, 2)
        sh_25 = round((v25 / tot_yoy * 100.0) if tot_yoy > 0 else 0.0, 2)
        var_pp = round(sh_26 - sh_25, 2)

        canais_list.append({
            'canal': r['canal'], 'grupo': r['canal_grupo'],
            'venda_jul_26': v26, 'venda_jun_26': v26_06, 'venda_jul_25': v25,
            'mom_pct': m_pct, 'mom_rs': m_rs, 'yoy_pct': y_pct, 'yoy_rs': y_rs,
            'part_jul_26': sh_26, 'part_jun_26': sh_26_06, 'part_jul_25': sh_25, 'var_pp': var_pp
        })

    canais_list.sort(key=lambda x: x['venda_jul_26'], reverse=True)
    with open(os.path.join(DATA_DIR, 'canais_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(canais_list, f, ensure_ascii=False, indent=2)

    # 2. CANAIS BY HIERARQUIA
    print("Processing canais_by_hierarquia.json...")
    grp_c_hier = df.groupby(['grupo', 'subgrupo', 'linha', 'laboratorio', 'canal', 'canal_grupo'], as_index=False).agg({
        'venda_ago_26': 'sum', 'venda_jul_26': 'sum', 'venda_ago_25': 'sum'
    })

    canais_hier_list = []
    for _, r in grp_c_hier.iterrows():
        v26 = round(float(r['venda_ago_26']), 2)
        v26_06 = round(float(r['venda_jul_26']), 2)
        v25 = round(float(r['venda_ago_25']), 2)

        canais_hier_list.append({
            'diretor': '', 'distrital': '',
            'grupo': r['grupo'], 'subgrupo': r['subgrupo'], 'linha': r['linha'], 'laboratorio': r['laboratorio'],
            'canal': r['canal'], 'canal_grupo': r['canal_grupo'],
            'v26': v26, 'v26_06': v26_06, 'v25': v25
        })

    with open(os.path.join(DATA_DIR, 'canais_by_hierarquia.json'), 'w', encoding='utf-8') as f:
        json.dump(canais_hier_list, f, ensure_ascii=False, separators=(',', ':'))

    # 3. CATEGORIAS SUMMARY
    print("Processing categorias_summary.json...")
    grp_cat = df.groupby(['diretor', 'distrital', 'grupo'], as_index=False).agg({
        'venda_ago_26': 'sum', 'venda_jul_26': 'sum', 'venda_ago_25': 'sum'
    })
    df_dig = df[df['is_digital']].groupby(['diretor', 'distrital', 'grupo'], as_index=False).agg({
        'venda_ago_26': 'sum', 'venda_jul_26': 'sum', 'venda_ago_25': 'sum'
    })
    df_dt = df[df['is_dt']].groupby(['diretor', 'distrital', 'grupo'], as_index=False).agg({
        'venda_ago_26': 'sum', 'venda_jul_26': 'sum', 'venda_ago_25': 'sum'
    })

    dig_map = {(r['diretor'], r['distrital'], r['grupo']): r for _, r in df_dig.iterrows()}
    dt_map = {(r['diretor'], r['distrital'], r['grupo']): r for _, r in df_dt.iterrows()}

    cat_records = []
    for _, r in grp_cat.iterrows():
        k = (r['diretor'], r['distrital'], r['grupo'])
        v26 = round(float(r['venda_ago_26']), 2)
        v26_06 = round(float(r['venda_jul_26']), 2)
        v25 = round(float(r['venda_ago_25']), 2)
        m_pct, m_rs = calc_growth(v26, v26_06)
        y_pct, y_rs = calc_growth(v26, v25)

        r_dig = dig_map.get(k)
        v_dig26 = round(float(r_dig['venda_ago_26']), 2) if r_dig is not None else 0.0
        v_dig26_06 = round(float(r_dig['venda_jul_26']), 2) if r_dig is not None else 0.0
        v_dig25 = round(float(r_dig['venda_ago_25']), 2) if r_dig is not None else 0.0

        r_dt = dt_map.get(k)
        v_dt26 = round(float(r_dt['venda_ago_26']), 2) if r_dt is not None else 0.0
        v_dt26_06 = round(float(r_dt['venda_jul_26']), 2) if r_dt is not None else 0.0
        v_dt25 = round(float(r_dt['venda_ago_25']), 2) if r_dt is not None else 0.0

        cat_records.append({
            'diretor': r['diretor'], 'distrital': r['distrital'], 'grupo': r['grupo'],
            'venda_jul_26': v26, 'venda_jun_26': v26_06, 'venda_jul_25': v25,
            'venda_digital_jul_26': v_dig26, 'venda_digital_jun_26': v_dig26_06, 'venda_digital_jul_25': v_dig25,
            'venda_dt_jul_26': v_dt26, 'venda_dt_jun_26': v_dt26_06, 'venda_dt_jul_25': v_dt25,
            'mom_pct': m_pct, 'mom_rs': m_rs, 'yoy_pct': y_pct, 'yoy_rs': y_rs
        })

    with open(os.path.join(DATA_DIR, 'categorias_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(cat_records, f, ensure_ascii=False, indent=2)

    # 4. HIERARQUIA DETALHADA
    print("Processing hierarquia_detalhada.json...")
    grp_hier = df.groupby(['grupo', 'subgrupo', 'linha', 'laboratorio'], as_index=False).agg({
        'venda_ago_26': 'sum', 'venda_jul_26': 'sum', 'venda_ago_25': 'sum'
    })
    df_hier_dig = df[df['is_digital']].groupby(['grupo', 'subgrupo', 'linha', 'laboratorio'], as_index=False).agg({
        'venda_ago_26': 'sum', 'venda_jul_26': 'sum', 'venda_ago_25': 'sum'
    })
    df_hier_dt = df[df['is_dt']].groupby(['grupo', 'subgrupo', 'linha', 'laboratorio'], as_index=False).agg({
        'venda_ago_26': 'sum', 'venda_jul_26': 'sum', 'venda_ago_25': 'sum'
    })

    h_dig_map = {(r['grupo'], r['subgrupo'], r['linha'], r['laboratorio']): r for _, r in df_hier_dig.iterrows()}
    h_dt_map = {(r['grupo'], r['subgrupo'], r['linha'], r['laboratorio']): r for _, r in df_hier_dt.iterrows()}

    hier_records = []
    for _, r in grp_hier.iterrows():
        hk = (r['grupo'], r['subgrupo'], r['linha'], r['laboratorio'])
        v26 = round(float(r['venda_ago_26']), 2)
        v26_06 = round(float(r['venda_jul_26']), 2)
        v25 = round(float(r['venda_ago_25']), 2)
        m_pct, m_rs = calc_growth(v26, v26_06)
        y_pct, y_rs = calc_growth(v26, v25)

        r_dig = h_dig_map.get(hk)
        v_dig26 = round(float(r_dig['venda_ago_26']), 2) if r_dig is not None else 0.0
        v_dig26_06 = round(float(r_dig['venda_jul_26']), 2) if r_dig is not None else 0.0
        v_dig25 = round(float(r_dig['venda_ago_25']), 2) if r_dig is not None else 0.0

        r_dt = h_dt_map.get(hk)
        v_dt26 = round(float(r_dt['venda_ago_26']), 2) if r_dt is not None else 0.0
        v_dt26_06 = round(float(r_dt['venda_jul_26']), 2) if r_dt is not None else 0.0
        v_dt25 = round(float(r_dt['venda_ago_25']), 2) if r_dt is not None else 0.0

        hier_records.append({
            'diretor': '', 'distrital': '', 'grupo': r['grupo'],
            'subgrupo': r['subgrupo'], 'linha': r['linha'], 'laboratorio': r['laboratorio'],
            'venda_jul_26': v26, 'venda_jun_26': v26_06, 'venda_jul_25': v25,
            'venda_digital_jul_26': v_dig26, 'venda_digital_jun_26': v_dig26_06, 'venda_digital_jul_25': v_dig25,
            'venda_dt_jul_26': v_dt26, 'venda_dt_jun_26': v_dt26_06, 'venda_dt_jul_25': v_dt25,
            'mom_pct': m_pct, 'mom_rs': m_rs, 'yoy_pct': y_pct, 'yoy_rs': y_rs
        })

    with open(os.path.join(DATA_DIR, 'hierarquia_detalhada.json'), 'w', encoding='utf-8') as f:
        json.dump(hier_records, f, ensure_ascii=False, indent=2)

    # 5. FILTROS & KPIS
    print("Processing filtros and KPIs...")

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

    tot_digital_cur = round(float(df[df['is_digital']]['venda_ago_26'].sum()), 2)
    tot_digital_mom = round(float(df[df['is_digital']]['venda_jul_26'].sum()), 2)
    tot_digital_yoy = round(float(df[df['is_digital']]['venda_ago_25'].sum()), 2)

    tot_dt_cur = round(float(df[df['is_dt']]['venda_ago_26'].sum()), 2)
    tot_dt_mom = round(float(df[df['is_dt']]['venda_jul_26'].sum()), 2)
    tot_dt_yoy = round(float(df[df['is_dt']]['venda_ago_25'].sum()), 2)

    mom_pct, mom_rs = calc_growth(tot_cur, tot_mom)
    yoy_pct, yoy_rs = calc_growth(tot_cur, tot_yoy)

    executive_kpis = {
        'venda_jul_26': tot_cur, 'venda_jun_26': tot_mom, 'venda_jul_25': tot_yoy,
        'venda_digital_jul_26': tot_digital_cur, 'venda_digital_jun_26': tot_digital_mom, 'venda_digital_jul_25': tot_digital_yoy,
        'venda_dt_jul_26': tot_dt_cur, 'venda_dt_jun_26': tot_dt_mom, 'venda_dt_jul_25': tot_dt_yoy,
        'mom_pct': mom_pct, 'mom_rs': mom_rs,
        'yoy_pct': yoy_pct, 'yoy_rs': yoy_rs,
        'periodo_info': {
            'periodo_str': '01 a 17/08/2026',
            'dias_fechados': 17
        }
    }
    with open(os.path.join(DATA_DIR, 'executive_kpis.json'), 'w', encoding='utf-8') as f:
        json.dump(executive_kpis, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*70}")
    print(f"TODOS OS ARQUIVOS JSON DE AGOSTO GERADOS EM {time.time() - t0:.2f}s!")
    print(f"Output: {DATA_DIR}")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
