"""
build_setembro_dashboard.py — Compila metas (Excel por Distrital × Linha) + realizado (Qlik Sense)
em um JSON final estruturado para o dashboard de Setembro/2026.
Gera visão Macro Empresa, Categorias, Diretorias Regionais e Distritais detalhados.
"""
import os, sys, json
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'setembro')

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calc_desvio(meta, realizado):
    desvio_rs = round(realizado - meta, 2)
    desvio_pct = round((realizado / meta - 1) * 100, 2) if meta > 0 else 0.0
    return desvio_rs, desvio_pct

def get_status(desvio_pct, d_max):
    if d_max == 0: return 'aguardando'
    if desvio_pct >= 0: return 'acima'
    if desvio_pct >= -5: return 'alerta'
    return 'abaixo'

def build_dashboard():
    print("\n" + "=" * 70)
    print("  COMPILANDO DASHBOARD SETEMBRO — METAS & HIERARQUIA ORGANIZACIONAL")
    print("=" * 70)

    # 1. Carregar Metas Distrital × Linha e Curva Diária
    metas_micro = load_json('metas_distrital_linha.json')
    metas_macro = load_json('metas_por_linha_dia.json')
    curva = load_json('curva_diaria.json')
    hier_detalhada = load_json('hierarquia_detalhada.json')
    realizado_info = load_json('realizado_por_linha_dia.json') or {}
    kpis_info = load_json('executive_kpis.json') or {}

    if not metas_micro or not curva:
        print("  ❌ Erro: Rode load_metas_setembro.py primeiro!")
        return

    # 2. Identificar D-Max do Realizado Dinamicamente
    d_max = realizado_info.get('d_max')
    if not d_max:
        d_max = kpis_info.get('periodo_info', {}).get('dias_fechados')
    if not d_max:
        from datetime import date
        today_day = date.today().day
        d_max = max(1, today_day - 1 if today_day > 1 else 1)

    d_max = min(max(1, int(d_max)), len(curva))
    pct_acum_dmax = curva[d_max - 1]['pct_acum'] if d_max <= len(curva) else (d_max / 30.0)

    print(f"  📅 D-Max: Dia {d_max}/30 ({pct_acum_dmax*100:.2f}% do mês esperado)")

    # 3. Processar Realizado Qlik por (Diretor, Distrital, Grupo, Subgrupo, Linha)
    df_hier = pd.DataFrame(hier_detalhada) if hier_detalhada else pd.DataFrame()
    
    real_dist_linha_map = {}
    if not df_hier.empty:
        for _, r in df_hier.iterrows():
            dist = str(r.get('distrital', '')).strip()
            linha = str(r.get('linha', '')).strip()
            val = float(r.get('venda_jul_26', 0.0))
            key = (dist, linha)
            real_dist_linha_map[key] = real_dist_linha_map.get(key, 0.0) + val

    # 4. Processar Micro (Distrital × Linha)
    df_micro = pd.DataFrame(metas_micro)
    
    # Atribuir realizado de cada Distrital × Linha
    df_micro['real_acum_dmax'] = df_micro.apply(
        lambda r: round(real_dist_linha_map.get((r['distrital'], r['linha']), 0.0), 2), axis=1
    )
    df_micro['meta_acum_dmax'] = df_micro['meta_mensal'].apply(lambda v: round(v * pct_acum_dmax, 2))
    df_micro['desvio_rs'] = df_micro['real_acum_dmax'] - df_micro['meta_acum_dmax']
    df_micro['desvio_pct'] = df_micro.apply(
        lambda r: round((r['real_acum_dmax'] / r['meta_acum_dmax'] - 1) * 100, 2) if r['meta_acum_dmax'] > 0 else 0.0, axis=1
    )
    df_micro['ating_pct'] = df_micro.apply(
        lambda r: round(r['real_acum_dmax'] / r['meta_acum_dmax'] * 100, 2) if r['meta_acum_dmax'] > 0 else 0.0, axis=1
    )
    df_micro['status'] = df_micro['desvio_pct'].apply(lambda v: get_status(v, d_max))

    # 5. Estruturar Macro Empresa
    meta_empresa_mensal = round(df_micro['meta_mensal'].sum(), 2)
    meta_empresa_dmax = round(df_micro['meta_acum_dmax'].sum(), 2)
    real_empresa_dmax = round(df_micro['real_acum_dmax'].sum(), 2)
    desvio_emp_rs, desvio_emp_pct = calc_desvio(meta_empresa_dmax, real_empresa_dmax)
    ating_emp_pct = round(real_empresa_dmax / meta_empresa_dmax * 100, 2) if meta_empresa_dmax > 0 else 0.0

    # Evolução Diária da Empresa (30 dias)
    evolucao_meta_acum = [round(c['meta_acum'], 2) for c in curva]
    evolucao_meta_diaria = [round(c.get('meta_dia', 0.0), 2) for c in curva]
    
    evolucao_real_acum = [0.0] * 30
    evolucao_real_diaria = [0.0] * 30
    desvio_diario_pct = [None] * 30
    desvio_diario_rs = [None] * 30
    ating_diario_pct = [None] * 30

    total_emp_dia = realizado_info.get('total_empresa_dia', [])
    total_emp_acum = realizado_info.get('total_empresa_acum', [])

    for idx in range(30):
        if idx < d_max:
            r_dia = round(total_emp_dia[idx], 2) if idx < len(total_emp_dia) else 0.0
            r_acum = round(total_emp_acum[idx], 2) if idx < len(total_emp_acum) else 0.0
            m_dia = evolucao_meta_diaria[idx]
            
            evolucao_real_diaria[idx] = r_dia
            evolucao_real_acum[idx] = r_acum
            
            if m_dia > 0:
                d_pct = round(((r_dia / m_dia) - 1.0) * 100.0, 2)
                d_rs = round(r_dia - m_dia, 2)
                at_pct = round((r_dia / m_dia) * 100.0, 2)
            else:
                d_pct = 0.0
                d_rs = 0.0
                at_pct = 0.0
                
            desvio_diario_pct[idx] = d_pct
            desvio_diario_rs[idx] = d_rs
            ating_diario_pct[idx] = at_pct

            if idx < len(curva):
                curva[idx]['real_dia'] = r_dia
                curva[idx]['real_acum'] = r_acum
                curva[idx]['desvio_dia_pct'] = d_pct
                curva[idx]['desvio_dia_rs'] = d_rs
                curva[idx]['ating_dia_pct'] = at_pct

    empresa_data = {
        'meta_mensal': meta_empresa_mensal,
        'meta_acum_dmax': meta_empresa_dmax,
        'real_acum_dmax': real_empresa_dmax,
        'desvio_rs': desvio_emp_rs,
        'desvio_pct': desvio_emp_pct,
        'ating_pct': ating_emp_pct,
        'projecao_runrate': round((real_empresa_dmax / d_max) * 30, 2) if d_max > 0 else 0.0,
        'projecao_linear': round(meta_empresa_mensal * (ating_emp_pct / 100.0), 2),
        'evolucao_meta': evolucao_meta_acum,
        'evolucao_real': evolucao_real_acum,
        'evolucao_meta_diaria': evolucao_meta_diaria,
        'evolucao_real_diaria': evolucao_real_diaria,
        'desvio_diario_pct': desvio_diario_pct,
        'desvio_diario_rs': desvio_diario_rs,
        'ating_diario_pct': ating_diario_pct
    }

    # 6. Estruturar Grupos / Categorias da Empresa
    grupos_empresa = []
    for grupo_nome, grp_df in df_micro.groupby('grupo'):
        g_meta_m = grp_df['meta_mensal'].sum()
        g_meta_d = grp_df['meta_acum_dmax'].sum()
        g_real_d = grp_df['real_acum_dmax'].sum()
        d_rs, d_pct = calc_desvio(g_meta_d, g_real_d)
        at_pct = round(g_real_d / g_meta_d * 100, 2) if g_meta_d > 0 else 0.0

        grupos_empresa.append({
            'grupo': grupo_nome,
            'meta_mensal': round(g_meta_m, 2),
            'meta_acum_dmax': round(g_meta_d, 2),
            'real_acum_dmax': round(g_real_d, 2),
            'desvio_rs': d_rs,
            'desvio_pct': d_pct,
            'ating_pct': at_pct,
            'share_meta': round(g_meta_m / meta_empresa_mensal * 100, 2) if meta_empresa_mensal > 0 else 0.0,
            'share_real': round(g_real_d / real_empresa_dmax * 100, 2) if real_empresa_dmax > 0 else 0.0,
            'status': get_status(d_pct, d_max),
            'total_linhas': len(grp_df)
        })
    grupos_empresa.sort(key=lambda x: x['meta_mensal'], reverse=True)

    # 7. Estruturar Linhas da Empresa
    linhas_empresa = []
    for linha_nome, l_df in df_micro.groupby('linha'):
        l_meta_m = l_df['meta_mensal'].sum()
        l_meta_d = l_df['meta_acum_dmax'].sum()
        l_real_d = l_df['real_acum_dmax'].sum()
        d_rs, d_pct = calc_desvio(l_meta_d, l_real_d)
        at_pct = round(l_real_d / l_meta_d * 100, 2) if l_meta_d > 0 else 0.0
        familia = l_df['familia'].iloc[0] if not l_df.empty else ''
        grupo = l_df['grupo'].iloc[0] if not l_df.empty else ''
        subgrupo = l_df['subgrupo'].iloc[0] if not l_df.empty else ''

        linhas_empresa.append({
            'linha': linha_nome,
            'familia': familia,
            'grupo': grupo,
            'subgrupo': subgrupo,
            'categoria': grupo,
            'meta_mensal': round(l_meta_m, 2),
            'meta_acum_dmax': round(l_meta_d, 2),
            'real_acum_dmax': round(l_real_d, 2),
            'desvio_rs': d_rs,
            'desvio_pct': d_pct,
            'ating_pct': at_pct,
            'status': get_status(d_pct, d_max)
        })
    linhas_empresa.sort(key=lambda x: x['meta_mensal'], reverse=True)

    # 8. Estruturar Diretoria ➔ Distrital ➔ Grupo ➔ Linha
    diretorias_list = []
    distritais_list = []

    for dir_nome, grp_dir in df_micro.groupby('diretor'):
        d_meta_m = grp_dir['meta_mensal'].sum()
        d_meta_d = grp_dir['meta_acum_dmax'].sum()
        d_real_d = grp_dir['real_acum_dmax'].sum()
        d_desv_rs, d_desv_pct = calc_desvio(d_meta_d, d_real_d)
        d_ating = round(d_real_d / d_meta_d * 100, 2) if d_meta_d > 0 else 0.0

        # Distritais desta diretoria
        distritais_da_diretoria = []
        for dist_nome, grp_dist in grp_dir.groupby('distrital'):
            dt_meta_m = grp_dist['meta_mensal'].sum()
            dt_meta_d = grp_dist['meta_acum_dmax'].sum()
            dt_real_d = grp_dist['real_acum_dmax'].sum()
            dt_desv_rs, dt_desv_pct = calc_desvio(dt_meta_d, dt_real_d)
            dt_ating = round(dt_real_d / dt_meta_d * 100, 2) if dt_meta_d > 0 else 0.0

            # Grupos dentro deste Distrital
            grupos_do_distrital = []
            for g_nome, grp_g in grp_dist.groupby('grupo'):
                # Linhas dentro do Grupo do Distrital
                linhas_do_grupo = []
                for _, r_lin in grp_g.iterrows():
                    linhas_do_grupo.append({
                        'linha': r_lin['linha'],
                        'familia': r_lin['familia'],
                        'subgrupo': r_lin['subgrupo'],
                        'meta_mensal': round(r_lin['meta_mensal'], 2),
                        'meta_acum_dmax': round(r_lin['meta_acum_dmax'], 2),
                        'real_acum_dmax': round(r_lin['real_acum_dmax'], 2),
                        'desvio_rs': round(r_lin['desvio_rs'], 2),
                        'desvio_pct': r_lin['desvio_pct'],
                        'ating_pct': r_lin['ating_pct'],
                        'status': r_lin['status']
                    })
                linhas_do_grupo.sort(key=lambda x: x['meta_mensal'], reverse=True)

                gm = round(sum(l['meta_mensal'] for l in linhas_do_grupo), 2)
                gd = round(sum(l['meta_acum_dmax'] for l in linhas_do_grupo), 2)
                gr = round(sum(l['real_acum_dmax'] for l in linhas_do_grupo), 2)
                g_d_rs, g_d_pct = calc_desvio(gd, gr)
                g_at = round(gr / gd * 100, 2) if gd > 0 else 0.0

                grupos_do_distrital.append({
                    'grupo': g_nome,
                    'meta_mensal': gm,
                    'meta_acum_dmax': gd,
                    'real_acum_dmax': gr,
                    'desvio_rs': g_d_rs,
                    'desvio_pct': g_d_pct,
                    'ating_pct': g_at,
                    'status': get_status(g_d_pct, d_max),
                    'total_linhas': len(linhas_do_grupo),
                    'linhas': linhas_do_grupo
                })
            grupos_do_distrital.sort(key=lambda x: x['meta_mensal'], reverse=True)

            dt_meta_m = round(sum(g['meta_mensal'] for g in grupos_do_distrital), 2)
            dt_meta_d = round(sum(g['meta_acum_dmax'] for g in grupos_do_distrital), 2)
            dt_real_d = round(sum(g['real_acum_dmax'] for g in grupos_do_distrital), 2)
            dt_desv_rs, dt_desv_pct = calc_desvio(dt_meta_d, dt_real_d)
            dt_ating = round(dt_real_d / dt_meta_d * 100, 2) if dt_meta_d > 0 else 0.0

            dist_obj = {
                'distrital': dist_nome,
                'diretor': dir_nome,
                'meta_mensal': dt_meta_m,
                'meta_acum_dmax': dt_meta_d,
                'real_acum_dmax': dt_real_d,
                'desvio_rs': dt_desv_rs,
                'desvio_pct': dt_desv_pct,
                'ating_pct': dt_ating,
                'status': get_status(dt_desv_pct, d_max),
                'share_empresa_pct': round(dt_meta_m / meta_empresa_mensal * 100, 2),
                'total_linhas': len(grp_dist),
                'grupos': grupos_do_distrital
            }
            distritais_da_diretoria.append(dist_obj)
            distritais_list.append(dist_obj)

        distritais_da_diretoria.sort(key=lambda x: x['meta_mensal'], reverse=True)

        d_meta_m = round(sum(dt['meta_mensal'] for dt in distritais_da_diretoria), 2)
        d_meta_d = round(sum(dt['meta_acum_dmax'] for dt in distritais_da_diretoria), 2)
        d_real_d = round(sum(dt['real_acum_dmax'] for dt in distritais_da_diretoria), 2)
        d_desv_rs, d_desv_pct = calc_desvio(d_meta_d, d_real_d)
        d_ating = round(d_real_d / d_meta_d * 100, 2) if d_meta_d > 0 else 0.0

        diretorias_list.append({
            'diretor': dir_nome,
            'meta_mensal': d_meta_m,
            'meta_acum_dmax': d_meta_d,
            'real_acum_dmax': d_real_d,
            'desvio_rs': d_desv_rs,
            'desvio_pct': d_desv_pct,
            'ating_pct': d_ating,
            'status': get_status(d_desv_pct, d_max),
            'share_empresa_pct': round(d_meta_m / meta_empresa_mensal * 100, 2),
            'total_distritais': len(distritais_da_diretoria),
            'distritais': distritais_da_diretoria
        })

    diretorias_list.sort(key=lambda x: x['meta_mensal'], reverse=True)
    distritais_list.sort(key=lambda x: x['ating_pct'], reverse=True) # Ranking de atingimento

    # Sincronizar Empresa Meta D-1 com a soma exata dos distritais e diretorias
    empresa_data['meta_acum_dmax'] = round(sum(d['meta_acum_dmax'] for d in diretorias_list), 2)
    empresa_data['meta_mensal'] = round(sum(d['meta_mensal'] for d in diretorias_list), 2)
    empresa_data['real_acum_dmax'] = round(sum(d['real_acum_dmax'] for d in diretorias_list), 2)
    desv_emp_rs, desv_emp_pct = calc_desvio(empresa_data['meta_acum_dmax'], empresa_data['real_acum_dmax'])
    empresa_data['desvio_rs'] = desv_emp_rs
    empresa_data['desvio_pct'] = desv_emp_pct
    empresa_data['ating_pct'] = round(empresa_data['real_acum_dmax'] / empresa_data['meta_acum_dmax'] * 100, 2)

    # 9. Contagem de status por Linha Empresa
    status_count = {'acima': 0, 'alerta': 0, 'abaixo': 0, 'aguardando': 0}
    for l in linhas_empresa:
        status_count[l['status']] = status_count.get(l['status'], 0) + 1

    # 10. Consolidar payload do Dashboard
    dashboard_payload = {
        'd_max': d_max,
        'dias_totais': 30,
        'dias_restantes': 30 - d_max,
        'periodo_str': f"01 a {d_max:02d}/09/2026",
        'empresa': empresa_data,
        'grupos': grupos_empresa,
        'linhas': linhas_empresa,
        'diretorias': diretorias_list,
        'distritais': distritais_list,
        'status_count': status_count,
        'curva_diaria': curva
    }

    out_file = os.path.join(DATA_DIR, 'dashboard_setembro.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(dashboard_payload, f, ensure_ascii=False)

    size_kb = os.path.getsize(out_file) / 1024
    print(f"  [OK] dashboard_setembro.json gerado com sucesso ({size_kb:.1f} KB)")
    print(f"       -> Empresa Meta: R$ {meta_empresa_mensal:,.2f} | Real D{d_max}: R$ {real_empresa_dmax:,.2f} ({ating_emp_pct:.1f}%)")
    print(f"       -> Diretorias: {len(diretorias_list)} | Distritais: {len(distritais_list)} | Grupos: {len(grupos_empresa)} | Linhas: {len(linhas_empresa)}")
    print("=" * 70)

if __name__ == '__main__':
    build_dashboard()
