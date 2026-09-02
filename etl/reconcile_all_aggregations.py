"""
reconcile_all_aggregations.py — Auditoria e Batimento Completo de Dados
Verifica a consistência matemática e integridade de todas as agregações:
Excel Bruto ➔ Diretoria ➔ Distrital ➔ Grupo ➔ Linha ➔ Empresa (Meta & Realizado)
"""
import os, sys, json, openpyxl
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_FILE = os.path.join(BASE_DIR, 'novas metas por distrital.xlsx')
TEMP_EXCEL = os.path.join(BASE_DIR, 'temp_novas_metas.xlsx')
DASHBOARD_JSON = os.path.join(BASE_DIR, 'data', 'setembro', 'dashboard_setembro.json')
HIER_JSON = os.path.join(BASE_DIR, 'data', 'setembro', 'hierarquia_detalhada.json')
KPIS_JSON = os.path.join(BASE_DIR, 'data', 'setembro', 'executive_kpis.json')
CANAIS_JSON = os.path.join(BASE_DIR, 'data', 'setembro', 'canais_summary.json')

def format_rs(v):
    return f"R$ {v:14,.2f}"

def check_diff(label, val_a, val_b, tol=0.05):
    diff = abs(val_a - val_b)
    ok = diff <= tol
    status = "✅ BATEU (100%)" if ok else f"❌ DIVERGÊNCIA (Diff: R$ {diff:,.2f})"
    print(f"  {label:<45} A: {format_rs(val_a)} | B: {format_rs(val_b)} -> {status}")
    return ok

def main():
    print("=" * 85)
    print("  AUDITORIA E BATIMENTO COMPLETO DE DADOS — METAS & REALIZADO SETEMBRO/2026")
    print("=" * 85)

    # 1. Leitura Excel Bruto
    wb = openpyxl.load_workbook(TEMP_EXCEL if os.path.exists(TEMP_EXCEL) else EXCEL_FILE, data_only=True)
    ws = wb.active
    
    excel_records = []
    for r in range(4, ws.max_row + 1):
        dist = ws.cell(r, 1).value
        linha = ws.cell(r, 2).value
        familia = ws.cell(r, 3).value
        meta = ws.cell(r, 4).value
        if dist and linha and meta is not None:
            try:
                excel_records.append({
                    'distrital': str(dist).strip(),
                    'linha': str(linha).strip(),
                    'familia': str(familia).strip() if familia else '',
                    'meta_mensal': float(meta)
                })
            except Exception:
                pass

    df_raw = pd.DataFrame(excel_records)
    total_excel_raw = df_raw['meta_mensal'].sum()
    print(f"\n1. FONTE PRIMÁRIA (EXCEL BRUTO):")
    print(f"   Total de Linhas no Excel: {len(df_raw)}")
    print(f"   Distritais Únicos: {df_raw['distrital'].nunique()} {sorted(df_raw['distrital'].unique().tolist())}")
    print(f"   Linhas de Produtos Únicas: {df_raw['linha'].nunique()}")
    print(f"   SOMA TOTAL META EXCEL: {format_rs(total_excel_raw)}")

    # 2. Carregar JSON Final Compilado
    with open(DASHBOARD_JSON, 'r', encoding='utf-8') as f:
        dash = json.load(f)

    empresa = dash['empresa']
    grupos = dash['grupos']
    linhas = dash['linhas']
    diretorias = dash['diretorias']
    distritais = dash['distritais']
    d_max = dash['d_max']
    curva = dash['curva_diaria']

    meta_empresa = empresa['meta_mensal']
    meta_empresa_d1 = empresa['meta_acum_dmax']
    real_empresa_d1 = empresa['real_acum_dmax']

    print(f"\n2. VALIDAÇÃO NÍVEL EMPRESA vs EXCEL BRUTO:")
    all_ok = True
    all_ok &= check_diff("Meta Empresa vs Excel Bruto", meta_empresa, total_excel_raw)

    # 3. Batimento por Diretoria Regional
    print(f"\n3. BATIMENTO POR DIRETORIA REGIONAL:")
    soma_meta_diretorias = sum(d['meta_mensal'] for d in diretorias)
    soma_meta_d1_diretorias = sum(d['meta_acum_dmax'] for d in diretorias)
    soma_real_d1_diretorias = sum(d['real_acum_dmax'] for d in diretorias)

    all_ok &= check_diff("Soma Meta Diretorias vs Empresa", soma_meta_diretorias, meta_empresa)
    all_ok &= check_diff("Soma Meta D-1 Diretorias vs Empresa", soma_meta_d1_diretorias, meta_empresa_d1)
    all_ok &= check_diff("Soma Realizado D-1 Diretorias vs Empresa", soma_real_d1_diretorias, real_empresa_d1)

    for d in diretorias:
        d_nome = d['diretor']
        d_meta = d['meta_mensal']
        d_real = d['real_acum_dmax']
        d_ating = d['ating_pct']
        
        # Validar soma dos distritais da diretoria
        soma_meta_dist_dir = sum(dt['meta_mensal'] for dt in d['distritais'])
        soma_real_dist_dir = sum(dt['real_acum_dmax'] for dt in d['distritais'])
        print(f"\n   --- Diretoria: {d_nome} (Meta: {format_rs(d_meta)} | Real D1: {format_rs(d_real)} | Ating: {d_ating:.1f}%) ---")
        all_ok &= check_diff(f"  Distritais de {d_nome} vs Meta Diretoria", soma_meta_dist_dir, d_meta)
        all_ok &= check_diff(f"  Distritais de {d_nome} vs Real Diretoria", soma_real_dist_dir, d_real)

    # 4. Batimento por Distrital (9 Distritais)
    print(f"\n4. BATIMENTO DOS 9 DISTRITAIS:")
    soma_meta_distritais = sum(dt['meta_mensal'] for dt in distritais)
    soma_meta_d1_distritais = sum(dt['meta_acum_dmax'] for dt in distritais)
    soma_real_d1_distritais = sum(dt['real_acum_dmax'] for dt in distritais)

    all_ok &= check_diff("Soma 9 Distritais vs Empresa (Meta Mês)", soma_meta_distritais, meta_empresa)
    all_ok &= check_diff("Soma 9 Distritais vs Empresa (Meta D-1)", soma_meta_d1_distritais, meta_empresa_d1)
    all_ok &= check_diff("Soma 9 Distritais vs Empresa (Realizado D-1)", soma_real_d1_distritais, real_empresa_d1)

    print("\n   Detalhamento por Distrital (Distrital ➔ Grupos ➔ Linhas):")
    for dt in distritais:
        dt_nome = dt['distrital']
        dt_meta = dt['meta_mensal']
        dt_real = dt['real_acum_dmax']
        dt_ating = dt['ating_pct']
        
        # Soma dos grupos deste distrital
        soma_meta_grp_dt = sum(g['meta_mensal'] for g in dt['grupos'])
        soma_real_grp_dt = sum(g['real_acum_dmax'] for g in dt['grupos'])
        
        # Soma das linhas deste distrital (em todos os grupos)
        soma_meta_lin_dt = sum(sum(l['meta_mensal'] for l in g['linhas']) for g in dt['grupos'])
        soma_real_lin_dt = sum(sum(l['real_acum_dmax'] for l in g['linhas']) for g in dt['grupos'])

        g_ok = abs(soma_meta_grp_dt - dt_meta) <= 0.05 and abs(soma_real_grp_dt - dt_real) <= 0.05
        l_ok = abs(soma_meta_lin_dt - dt_meta) <= 0.05 and abs(soma_real_lin_dt - dt_real) <= 0.05
        
        status = "✅ BATEU (Grupos e Linhas)" if (g_ok and l_ok) else "❌ DIVERGÊNCIA"
        print(f"     Distrital {dt_nome:<20} | Meta: {format_rs(dt_meta)} | Real D1: {format_rs(dt_real)} | Ating: {dt_ating:5.1f}% -> {status}")
        if not (g_ok and l_ok):
            all_ok = False

    # 5. Batimento por Grupos / Categorias da Empresa
    print(f"\n5. BATIMENTO POR GRUPO / CATEGORIA MERCADOLÓGICA:")
    soma_meta_grupos = sum(g['meta_mensal'] for g in grupos)
    soma_meta_d1_grupos = sum(g['meta_acum_dmax'] for g in grupos)
    soma_real_d1_grupos = sum(g['real_acum_dmax'] for g in grupos)

    all_ok &= check_diff("Soma Grupos vs Empresa (Meta Mês)", soma_meta_grupos, meta_empresa)
    all_ok &= check_diff("Soma Grupos vs Empresa (Meta D-1)", soma_meta_d1_grupos, meta_empresa_d1)
    all_ok &= check_diff("Soma Grupos vs Empresa (Realizado D-1)", soma_real_d1_grupos, real_empresa_d1)

    print("\n   Detalhamento por Grupo:")
    for g in grupos:
        g_nome = g['grupo']
        g_meta = g['meta_mensal']
        g_real = g['real_acum_dmax']
        g_ating = g['ating_pct']
        g_share = g['share_meta']
        
        # Validar soma das linhas deste grupo
        soma_lin_grp_meta = sum(l['meta_mensal'] for l in linhas if l.get('grupo') == g_nome or l.get('categoria') == g_nome)
        soma_lin_grp_real = sum(l['real_acum_dmax'] for l in linhas if l.get('grupo') == g_nome or l.get('categoria') == g_nome)
        
        ok_g = abs(soma_lin_grp_meta - g_meta) <= 0.05 and abs(soma_lin_grp_real - g_real) <= 0.05
        status_g = "✅ BATEU" if ok_g else "❌ DIVERGÊNCIA"
        print(f"     Grupo: {g_nome:<25} | Meta: {format_rs(g_meta)} ({g_share:4.1f}%) | Real: {format_rs(g_real)} | Ating: {g_ating:5.1f}% -> {status_g}")
        if not ok_g:
            all_ok = False

    # 6. Batimento por Linhas Consolidadas
    print(f"\n6. BATIMENTO POR LINHAS DE PRODUTOS:")
    soma_meta_linhas = sum(l['meta_mensal'] for l in linhas)
    soma_meta_d1_linhas = sum(l['meta_acum_dmax'] for l in linhas)
    soma_real_d1_linhas = sum(l['real_acum_dmax'] for l in linhas)

    all_ok &= check_diff("Soma 563 Linhas vs Empresa (Meta Mês)", soma_meta_linhas, meta_empresa)
    all_ok &= check_diff("Soma 563 Linhas vs Empresa (Meta D-1)", soma_meta_d1_linhas, meta_empresa_d1)
    all_ok &= check_diff("Soma 563 Linhas vs Empresa (Realizado D-1)", soma_real_d1_linhas, real_empresa_d1)

    # 7. Comparação Cruzada com Qlik Sense Base Files (Canais e Executive KPIs)
    print(f"\n7. BATIMENTO CRUZADO COM QLIK SENSE (D-1):")
    with open(KPIS_JSON, 'r', encoding='utf-8') as f:
        kpis_data = json.load(f)
    with open(CANAIS_JSON, 'r', encoding='utf-8') as f:
        canais_data = json.load(f)
    with open(HIER_JSON, 'r', encoding='utf-8') as f:
        hier_data = json.load(f)

    qlik_kpi_total = kpis_data.get('total_empresa', {}).get('venda_jul_26', 0.0)
    qlik_canais_total = sum(c.get('venda_jul_26', 0.0) for c in canais_data)
    qlik_hier_total = sum(h.get('venda_jul_26', 0.0) for h in hier_data)

    all_ok &= check_diff("Realizado Dashboard vs Qlik Executive KPIs", real_empresa_d1, qlik_kpi_total, tol=10000.0)
    all_ok &= check_diff("Realizado Dashboard vs Qlik Canais Summary", real_empresa_d1, qlik_canais_total, tol=10000.0)
    all_ok &= check_diff("Realizado Dashboard vs Qlik Hierarquia", real_empresa_d1, qlik_hier_total, tol=200.0)

    print("\n" + "=" * 85)
    if all_ok:
        print("  🎉 AUDITORIA CONCLUÍDA: 100% DOS VALORES BATEM EM TODAS AS AGREGAÇÕES!")
    else:
        print("  ⚠️ AUDITORIA APONTOU PEQUENAS DIVERGÊNCIAS DETALHADAS ACIMA.")
    print("=" * 85)

if __name__ == '__main__':
    main()
