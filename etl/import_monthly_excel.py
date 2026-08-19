"""
import_monthly_excel.py — Importa a base oficial BASE DADOS.xlsx da pasta Acompanhamento Categorias preservando 100% dos registros.
"""
import os, sys, time, json
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TARGET_EXCEL = r'C:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\Acompanhamento Categorias\BASE DADOS.xlsx'

def clean_str(val):
    if pd.isna(val) or val is None: return ""
    return str(val).replace('\xa0', ' ').replace('\t', ' ').strip()

def calc_growth(cur, prev):
    diff = cur - prev
    pct = (diff / prev * 100.0) if prev > 0 else 0.0
    return round(pct, 2), round(diff, 2)

def get_channel_group(canal_name):
    c = str(canal_name).strip().upper()
    if c in ['APP', 'IFOOD', 'SITE', 'APP TELE ENTREGA', 'SITE TELE ENTREGA', 'E_COMMERCE', 'E-COMMERCE', 'RAPPI']:
        return 'digital'
    elif c in ['TELE ENCAMINHADA LOJAS', 'TELE VIZINHANÇA', 'TELE VIZINHANÇAS', 'VENDA TELE ENTREGA', 'VENDA TELE ENTREGA CENTRAL']:
        return 'tele'
    else:
        return 'loja'

def safe_sum_col(df, col_name):
    if col_name in df.columns:
        return round(float(df[col_name].sum()), 2)
    return 0.0

def safe_val_row(r, col_name):
    if col_name in r:
        return round(float(r[col_name]), 2)
    return 0.0

def run_import(excel_path=TARGET_EXCEL):
    t0 = time.time()
    print("=" * 70)
    print(f"IMPORTANDO BASE OFICIAL EXCEL: {excel_path}")
    print("=" * 70)

    if not os.path.exists(excel_path):
        print(f"[ERRO] Arquivo Excel não encontrado: {excel_path}")
        sys.exit(1)

    df_raw = pd.read_excel(excel_path, header=None)
    c_names = df_raw.iloc[0].values
    periods = df_raw.iloc[1].values

    cols = []
    for i in range(len(c_names)):
        if i < 8:
            cols.append(str(periods[i]).strip())
        else:
            ch = str(c_names[i]).strip()
            per = str(periods[i]).strip()
            cols.append(f"{ch}__{per}")

    df_data = df_raw.iloc[2:].copy()
    df_data.columns = cols

    rename_map = {
        'Desc_Grupo': 'grupo',
        'Desc_Subgrupo': 'subgrupo',
        'Desc_Linha': 'linha',
        'Laboratorio': 'laboratorio',
        'Diretor': 'diretor',
        'Distrital': 'distrital'
    }
    df_data = df_data.rename(columns=rename_map)

    for col in ['diretor', 'distrital', 'grupo', 'subgrupo', 'linha', 'laboratorio']:
        df_data[col] = df_data[col].fillna('').astype(str).str.replace('\xa0', ' ').str.strip()

    value_cols = [c for c in cols if '__' in c]
    channel_names = sorted(list(set([c.split('__')[0] for c in value_cols if c.split('__')[0] not in ['Canal', 'nan', ''] and not c.split('__')[0].startswith('Unnamed')])))

    for c in value_cols:
        df_data[c] = pd.to_numeric(df_data[c].replace('-', np.nan), errors='coerce').fillna(0.0)

    print("Agrupando hierarquia de produtos e canais...")

    # 1. CANAIS SUMMARY
    canais_summary = []
    tot_jul_26 = 0.0
    tot_jun_26 = 0.0
    tot_jul_25 = 0.0

    ch_totals = {}
    for ch in channel_names:
        c_grp = get_channel_group(ch)
        v25 = safe_sum_col(df_data, f"{ch}__2025-07")
        v26_06 = safe_sum_col(df_data, f"{ch}__2026-06")
        v26 = safe_sum_col(df_data, f"{ch}__2026-07")

        tot_jul_25 += v25
        tot_jun_26 += v26_06
        tot_jul_26 += v26

        ch_totals[ch] = {'grp': c_grp, 'v25': v25, 'v26_06': v26_06, 'v26': v26}

    for ch, d in ch_totals.items():
        v26 = d['v26']
        v26_06 = d['v26_06']
        v25 = d['v25']

        m_pct, m_rs = calc_growth(v26, v26_06)
        y_pct, y_rs = calc_growth(v26, v25)

        sh_26 = round((v26 / tot_jul_26 * 100.0) if tot_jul_26 > 0 else 0.0, 2)
        sh_26_06 = round((v26_06 / tot_jun_26 * 100.0) if tot_jun_26 > 0 else 0.0, 2)
        sh_25 = round((v25 / tot_jul_25 * 100.0) if tot_jul_25 > 0 else 0.0, 2)
        var_pp = round(sh_26 - sh_25, 2)

        canais_summary.append({
            'canal': ch, 'grupo': d['grp'],
            'venda_jul_26': v26, 'venda_jun_26': v26_06, 'venda_jul_25': v25,
            'mom_pct': m_pct, 'mom_rs': m_rs, 'yoy_pct': y_pct, 'yoy_rs': y_rs,
            'part_jul_26': sh_26, 'part_jun_26': sh_26_06, 'part_jul_25': sh_25, 'var_pp': var_pp
        })

    canais_summary.sort(key=lambda x: x['venda_jul_26'], reverse=True)
    with open(os.path.join(DATA_DIR, 'canais_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(canais_summary, f, ensure_ascii=False, indent=2)

    # 2. CANAIS BY HIERARQUIA (grupo, subgrupo, linha, canal)
    print("Processando canais_by_hierarquia.json...")
    grp_c_cols = ['grupo', 'subgrupo', 'linha']
    df_ch_agg = df_data.groupby(grp_c_cols, dropna=False, as_index=False)[value_cols].sum()

    canais_hier_records = []
    for _, r in df_ch_agg.iterrows():
        g_name = r['grupo']
        sg_name = r['subgrupo']
        l_name = r['linha']

        for ch in channel_names:
            v25 = safe_val_row(r, f"{ch}__2025-07")
            v26_06 = safe_val_row(r, f"{ch}__2026-06")
            v26 = safe_val_row(r, f"{ch}__2026-07")

            if v26 != 0.0 or v26_06 != 0.0 or v25 != 0.0:
                c_grp = get_channel_group(ch)
                canais_hier_records.append({
                    'diretor': '', 'distrital': '',
                    'grupo': g_name, 'subgrupo': sg_name, 'linha': l_name,
                    'canal': ch, 'canal_grupo': c_grp,
                    'v26': v26, 'v26_06': v26_06, 'v25': v25
                })

    with open(os.path.join(DATA_DIR, 'canais_by_hierarquia.json'), 'w', encoding='utf-8') as f:
        json.dump(canais_hier_records, f, ensure_ascii=False, indent=2)

    # 3. CATEGORIAS SUMMARY (diretor, distrital, grupo)
    print("Processando categorias_summary.json...")
    df_cat_agg = df_data.groupby(['diretor', 'distrital', 'grupo'], dropna=False, as_index=False)[value_cols].sum()

    cat_records = []
    for _, r in df_cat_agg.iterrows():
        v25 = round(sum(safe_val_row(r, f"{ch}__2025-07") for ch in channel_names), 2)
        v26_06 = round(sum(safe_val_row(r, f"{ch}__2026-06") for ch in channel_names), 2)
        v26 = round(sum(safe_val_row(r, f"{ch}__2026-07") for ch in channel_names), 2)

        dig_v25 = round(sum(safe_val_row(r, f"{ch}__2025-07") for ch in channel_names if get_channel_group(ch) == 'digital'), 2)
        dig_v26_06 = round(sum(safe_val_row(r, f"{ch}__2026-06") for ch in channel_names if get_channel_group(ch) == 'digital'), 2)
        dig_v26 = round(sum(safe_val_row(r, f"{ch}__2026-07") for ch in channel_names if get_channel_group(ch) == 'digital'), 2)

        dt_v25 = round(sum(safe_val_row(r, f"{ch}__2025-07") for ch in channel_names if get_channel_group(ch) in ['digital', 'tele']), 2)
        dt_v26_06 = round(sum(safe_val_row(r, f"{ch}__2026-06") for ch in channel_names if get_channel_group(ch) in ['digital', 'tele']), 2)
        dt_v26 = round(sum(safe_val_row(r, f"{ch}__2026-07") for ch in channel_names if get_channel_group(ch) in ['digital', 'tele']), 2)

        m_pct, m_rs = calc_growth(v26, v26_06)
        y_pct, y_rs = calc_growth(v26, v25)

        cat_records.append({
            'diretor': r['diretor'], 'distrital': r['distrital'], 'grupo': r['grupo'],
            'venda_jul_26': v26, 'venda_jun_26': v26_06, 'venda_jul_25': v25,
            'venda_digital_jul_26': dig_v26, 'venda_digital_jun_26': dig_v26_06, 'venda_digital_jul_25': dig_v25,
            'venda_dt_jul_26': dt_v26, 'venda_dt_jun_26': dt_v26_06, 'venda_dt_jul_25': dt_v25,
            'mom_pct': m_pct, 'mom_rs': m_rs, 'yoy_pct': y_pct, 'yoy_rs': y_rs
        })

    with open(os.path.join(DATA_DIR, 'categorias_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(cat_records, f, ensure_ascii=False, indent=2)

    # 4. HIERARQUIA DETALHADA (grupo, subgrupo, linha)
    print("Processando hierarquia_detalhada.json...")
    df_h_agg = df_data.groupby(['grupo', 'subgrupo', 'linha'], dropna=False, as_index=False)[value_cols].sum()

    hier_records = []
    for _, r in df_h_agg.iterrows():
        v25 = round(sum(safe_val_row(r, f"{ch}__2025-07") for ch in channel_names), 2)
        v26_06 = round(sum(safe_val_row(r, f"{ch}__2026-06") for ch in channel_names), 2)
        v26 = round(sum(safe_val_row(r, f"{ch}__2026-07") for ch in channel_names), 2)

        dig_v25 = round(sum(safe_val_row(r, f"{ch}__2025-07") for ch in channel_names if get_channel_group(ch) == 'digital'), 2)
        dig_v26_06 = round(sum(safe_val_row(r, f"{ch}__2026-06") for ch in channel_names if get_channel_group(ch) == 'digital'), 2)
        dig_v26 = round(sum(safe_val_row(r, f"{ch}__2026-07") for ch in channel_names if get_channel_group(ch) == 'digital'), 2)

        dt_v25 = round(sum(safe_val_row(r, f"{ch}__2025-07") for ch in channel_names if get_channel_group(ch) in ['digital', 'tele']), 2)
        dt_v26_06 = round(sum(safe_val_row(r, f"{ch}__2026-06") for ch in channel_names if get_channel_group(ch) in ['digital', 'tele']), 2)
        dt_v26 = round(sum(safe_val_row(r, f"{ch}__2026-07") for ch in channel_names if get_channel_group(ch) in ['digital', 'tele']), 2)

        m_pct, m_rs = calc_growth(v26, v26_06)
        y_pct, y_rs = calc_growth(v26, v25)

        hier_records.append({
            'diretor': '', 'distrital': '', 'grupo': r['grupo'],
            'subgrupo': r['subgrupo'], 'linha': r['linha'], 'laboratorio': '',
            'venda_jul_26': v26, 'venda_jun_26': v26_06, 'venda_jul_25': v25,
            'venda_digital_jul_26': dig_v26, 'venda_digital_jun_26': dig_v26_06, 'venda_digital_jul_25': dig_v25,
            'venda_dt_jul_26': dt_v26, 'venda_dt_jun_26': dt_v26_06, 'venda_dt_jul_25': dt_v25,
            'mom_pct': m_pct, 'mom_rs': m_rs, 'yoy_pct': y_pct, 'yoy_rs': y_rs
        })

    with open(os.path.join(DATA_DIR, 'hierarquia_detalhada.json'), 'w', encoding='utf-8') as f:
        json.dump(hier_records, f, ensure_ascii=False, indent=2)

    # 5. FILTROS & KPIS
    filtro_hier = {
        'diretores': sorted([x for x in df_data['diretor'].unique() if x]),
        'distritais': sorted([x for x in df_data['distrital'].unique() if x]),
        'grupos': sorted([x for x in df_data['grupo'].unique() if x]),
        'subgrupos': sorted([x for x in df_data['subgrupo'].unique() if x]),
        'linhas': sorted([x for x in df_data['linha'].unique() if x]),
        'laboratorios': sorted([x for x in df_data['laboratorio'].unique() if x])[:200]
    }
    with open(os.path.join(DATA_DIR, 'filtro_hierarquia.json'), 'w', encoding='utf-8') as f:
        json.dump(filtro_hier, f, ensure_ascii=False, indent=2)

    filtros_prod = {
        'grupos': sorted([x for x in df_data['grupo'].unique() if x]),
        'subgrupos': sorted([x for x in df_data['subgrupo'].unique() if x]),
        'linhas': sorted([x for x in df_data['linha'].unique() if x]),
        'laboratorios': sorted([x for x in df_data['laboratorio'].unique() if x])[:200]
    }
    with open(os.path.join(DATA_DIR, 'filtros_produto.json'), 'w', encoding='utf-8') as f:
        json.dump(filtros_prod, f, ensure_ascii=False, indent=2)

    dig_channels = [ch for ch in channel_names if get_channel_group(ch) == 'digital']
    dt_channels = [ch for ch in channel_names if get_channel_group(ch) in ['digital', 'tele']]

    tot_digital_jul_26 = round(sum(ch_totals[ch]['v26'] for ch in dig_channels), 2)
    tot_digital_jun_26 = round(sum(ch_totals[ch]['v26_06'] for ch in dig_channels), 2)
    tot_digital_jul_25 = round(sum(ch_totals[ch]['v25'] for ch in dig_channels), 2)

    tot_dt_jul_26 = round(sum(ch_totals[ch]['v26'] for ch in dt_channels), 2)
    tot_dt_jun_26 = round(sum(ch_totals[ch]['v26_06'] for ch in dt_channels), 2)
    tot_dt_jul_25 = round(sum(ch_totals[ch]['v25'] for ch in dt_channels), 2)

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

    print(f"\n[OK] BASE OFICIAL MENSAL PROCESSADA COM SUCESSO EM {time.time() - t0:.2f}s!")

if __name__ == '__main__':
    run_import()
