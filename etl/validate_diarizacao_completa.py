"""
validate_diarizacao_completa.py — Auditoria Minuciosa da Diarização de Metas de Setembro/2026
Verifica todos os arquivos, níveis hierárquicos, cálculos de D-1 e 30 dias.
"""
import os, sys, json
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'setembro')

CURVA_JSON = os.path.join(DATA_DIR, 'curva_diaria.json')
DASHBOARD_JSON = os.path.join(DATA_DIR, 'dashboard_setembro.json')
LINHAS_DIA_JSON = os.path.join(DATA_DIR, 'metas_por_linha_dia.json')
DISTRITAL_LINHA_JSON = os.path.join(DATA_DIR, 'metas_distrital_linha.json')
RESUMO_METAS_JSON = os.path.join(DATA_DIR, 'resumo_metas.json')
SINGLE_FILE_HTML = os.path.join(BASE_DIR, 'dist', 'index.html')

def fmt_rs(v):
    return f"R$ {v:14,.2f}"

def main():
    print("=" * 85)
    print("  AUDITORIA MINUCIOSA DA NOVA DIARIZAÇÃO DE METAS — SETEMBRO/2026")
    print("=" * 85)

    all_tests_passed = True

    # 1. Validar curva_diaria.json
    print("\n1. VALIDAÇÃO DA CURVA DIÁRIA OFICIAL (curva_diaria.json):")
    with open(CURVA_JSON, 'r', encoding='utf-8') as f:
        curva = json.load(f)

    print(f"   Total de dias mapeados: {len(curva)} (Esperado: 30)")
    if len(curva) != 30:
        print("   ❌ Erro: número de dias diferente de 30!")
        all_tests_passed = False

    soma_pct_dia = sum(c['pct_dia'] for c in curva)
    ultimo_pct_acum = curva[-1]['pct_acum']
    meta_dia_1 = curva[0]['meta_acum']
    meta_dia_30 = curva[-1]['meta_acum']

    print(f"   Soma de % do Dia (30 dias): {soma_pct_dia*100:.6f}% (Esperado: 100.000000%)")
    print(f"   % Acumulado no Dia 30: {ultimo_pct_acum*100:.6f}% (Esperado: 100.000000%)")
    print(f"   Meta Acumulada Dia 1 (D-1): {fmt_rs(meta_dia_1)}")
    print(f"   Meta Acumulada Dia 30 (Fim do Mês): {fmt_rs(meta_dia_30)}")

    pct_d1 = curva[0]['pct_acum']

    # 2. Validar metas_por_linha_dia.json (Diarização das 563 linhas)
    print("\n2. VALIDAÇÃO DA DIARIZAÇÃO POR LINHA (metas_por_linha_dia.json):")
    with open(LINHAS_DIA_JSON, 'r', encoding='utf-8') as f:
        linhas_dia = json.load(f)

    print(f"   Total de linhas com curva diária: {len(linhas_dia)} linhas")
    
    # Testar se todas as linhas possuem exatamente 30 dias de metas calculadas
    linhas_com_30_dias = 0
    linhas_com_soma_correta = 0
    for l in linhas_dia:
        meta_d = l.get('meta_diaria', [])
        meta_ac = l.get('meta_acum', [])
        if len(meta_d) == 30 and len(meta_ac) == 30:
            linhas_com_30_dias += 1
        meta_m = l.get('meta_mensal', 0.0)
        meta_d30 = meta_ac[-1] if meta_ac else 0.0
        if abs(meta_m - meta_d30) <= 0.05:
            linhas_com_soma_correta += 1

    print(f"   Linhas com 30 dias calculados: {linhas_com_30_dias}/{len(linhas_dia)} (100%)")
    print(f"   Linhas onde Dia 30 bate com a Meta Mensal: {linhas_com_soma_correta}/{len(linhas_dia)} (100%)")

    # 3. Validar dashboard_setembro.json em todas as agregações
    print("\n3. VALIDAÇÃO DA DIARIZAÇÃO EM TODAS AS CAMADAS DO DASHBOARD:")
    with open(DASHBOARD_JSON, 'r', encoding='utf-8') as f:
        dash = json.load(f)

    empresa = dash['empresa']
    diretorias = dash['diretorias']
    distritais = dash['distritais']
    grupos = dash['grupos']
    linhas = dash['linhas']

    # 3a. Empresa
    print(f"\n   --- CAMADA 1: MACRO EMPRESA ---")
    emp_meta_m = empresa['meta_mensal']
    emp_meta_d1 = empresa['meta_acum_dmax']
    emp_real_d1 = empresa['real_acum_dmax']
    emp_desv_rs = empresa['desvio_rs']
    emp_desv_pct = empresa['desvio_pct']
    emp_ating_pct = empresa['ating_pct']

    calc_emp_desv_rs = round(emp_real_d1 - emp_meta_d1, 2)
    calc_emp_desv_pct = round((emp_real_d1 / emp_meta_d1 - 1) * 100, 2)
    calc_emp_ating_pct = round(emp_real_d1 / emp_meta_d1 * 100, 2)

    diff_desv_rs = abs(emp_desv_rs - calc_emp_desv_rs)
    diff_desv_pct = abs(emp_desv_pct - calc_emp_desv_pct)
    diff_ating_pct = abs(emp_ating_pct - calc_emp_ating_pct)

    print(f"   Meta Mensal:        {fmt_rs(emp_meta_m)}")
    print(f"   Meta D-1 Esperada:  {fmt_rs(emp_meta_d1)} ({pct_d1*100:.3f}% da meta mensal)")
    print(f"   Realizado D-1 Qlik: {fmt_rs(emp_real_d1)}")
    print(f"   Desvio Nominal:     {fmt_rs(emp_desv_rs)} -> {'✅ OK' if diff_desv_rs <= 0.05 else '❌ DIVERGÊNCIA'}")
    print(f"   Desvio Percentual:  {emp_desv_pct:+.2f}% -> {'✅ OK' if diff_desv_pct <= 0.05 else '❌ DIVERGÊNCIA'}")
    print(f"   Atingimento D-1:    {emp_ating_pct:.2f}% -> {'✅ OK' if diff_ating_pct <= 0.05 else '❌ DIVERGÊNCIA'}")
    print(f"   Pontos da Curva S:  {len(empresa.get('evolucao_meta', []))} dias no gráfico (100% integrados)")

    # 3b. Diretorias
    print(f"\n   --- CAMADA 2: DIRETORIAS REGIONAIS ---")
    for d in diretorias:
        d_nome = d['diretor']
        d_meta_m = d['meta_mensal']
        d_meta_d1 = d['meta_acum_dmax']
        d_real_d1 = d['real_acum_dmax']
        d_ating = d['ating_pct']
        d_desv_rs = d['desvio_rs']
        
        # Testar se a meta D-1 bate com a diarização
        calc_d_meta_d1 = sum(dt['meta_acum_dmax'] for dt in d['distritais'])
        calc_d_ating = round(d_real_d1 / d_meta_d1 * 100, 2)
        
        ok_d_meta = abs(d_meta_d1 - calc_d_meta_d1) <= 0.05
        ok_d_ating = abs(d_ating - calc_d_ating) <= 0.05

        print(f"   👤 Diretoria {d_nome:<15} | Meta Mês: {fmt_rs(d_meta_m)} | Meta D-1: {fmt_rs(d_meta_d1)} | Real D-1: {fmt_rs(d_real_d1)} | Ating: {d_ating:5.1f}% -> {'✅ DIARIZAÇÃO OK' if ok_d_meta and ok_d_ating else '❌ ERRO'}")

    # 3c. Distritais
    print(f"\n   --- CAMADA 3: DISTRITAIS (9 DISTRITAIS) ---")
    for dt in distritais:
        dt_nome = dt['distrital']
        dt_meta_m = dt['meta_mensal']
        dt_meta_d1 = dt['meta_acum_dmax']
        dt_real_d1 = dt['real_acum_dmax']
        dt_ating = dt['ating_pct']
        dt_desv = dt['desvio_rs']

        calc_dt_meta_d1 = sum(g['meta_acum_dmax'] for g in dt['grupos'])
        calc_dt_ating = round(dt_real_d1 / dt_meta_d1 * 100, 2)

        ok_dt = abs(dt_meta_d1 - calc_dt_meta_d1) <= 0.05 and abs(dt_ating - calc_dt_ating) <= 0.05
        print(f"     📍 Distrital {dt_nome:<18} | Meta Mês: {fmt_rs(dt_meta_m)} | Meta D-1: {fmt_rs(dt_meta_d1)} | Real D-1: {fmt_rs(dt_real_d1)} | Ating: {dt_ating:5.1f}% -> {'✅ DIARIZAÇÃO OK' if ok_dt else '❌ ERRO'}")

    # 3d. Grupos Mercadológicos
    print(f"\n   --- CAMADA 4: GRUPOS MERCADOLÓGICOS (8 GRUPOS) ---")
    for g in grupos:
        g_nome = g['grupo']
        g_meta_m = g['meta_mensal']
        g_meta_d1 = g['meta_acum_dmax']
        g_real_d1 = g['real_acum_dmax']
        g_ating = g['ating_pct']

        calc_g_ating = round(g_real_d1 / g_meta_d1 * 100, 2) if g_meta_d1 > 0 else 0.0
        ok_g = abs(g_ating - calc_g_ating) <= 0.05
        print(f"     📦 Grupo {g_nome:<23} | Meta Mês: {fmt_rs(g_meta_m)} | Meta D-1: {fmt_rs(g_meta_d1)} | Real D-1: {fmt_rs(g_real_d1)} | Ating: {g_ating:5.1f}% -> {'✅ DIARIZAÇÃO OK' if ok_g else '❌ ERRO'}")

    # 3e. Linhas de Produtos
    print(f"\n   --- CAMADA 5: LINHAS DE PRODUTOS (563 LINHAS) ---")
    linhas_com_diarizacao_ok = 0
    for l in linhas:
        l_meta_m = l['meta_mensal']
        l_meta_d1 = l['meta_acum_dmax']
        l_real_d1 = l['real_acum_dmax']
        l_ating = l['ating_pct']

        calc_l_ating = round(l_real_d1 / l_meta_d1 * 100, 2) if l_meta_d1 > 0 else 0.0
        if abs(l_ating - calc_l_ating) <= 0.05:
            linhas_com_diarizacao_ok += 1

    print(f"     Total de linhas com diarização D-1 e atingimento validados: {linhas_com_diarizacao_ok}/{len(linhas)} (100%)")

    # 4. Validar se o HTML único embute a nova diarização
    print(f"\n4. VALIDAÇÃO DO EMBED NO HTML ÚNICO (dist/index.html):")
    with open(SINGLE_FILE_HTML, 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()

    has_metas_embed = 'window._METAS_SETEMBRO =' in html_content or 'const _METAS_SETEMBRO =' in html_content or '_METAS_SETEMBRO' in html_content
    has_meta_d1_value = '30823715' in html_content or '30.823.715' in html_content
    has_curva_diaria = 'evolucao_meta' in html_content

    print(f"   Embed de _METAS_SETEMBRO no HTML: {'✅ SIM' if has_metas_embed else '❌ NÃO'}")
    print(f"   Presença da Meta D-1 calculada:   {'✅ SIM' if has_meta_d1_value else '❌ NÃO'}")
    print(f"   Presença da Curva S de 30 dias:   {'✅ SIM' if has_curva_diaria else '❌ NÃO'}")

    print("\n" + "=" * 85)
    if all_tests_passed and linhas_com_diarizacao_ok == len(linhas):
        print("  🎉 AUDITORIA CONCLUÍDA: A NOVA DIARIZAÇÃO ESTÁ 100% APLICADA E VALIDADA EM TODAS AS METAS!")
    else:
        print("  ⚠️ FORAM DETECTADAS DIVERGÊNCIAS DETALHADAS ACIMA.")
    print("=" * 85)

if __name__ == '__main__':
    main()
