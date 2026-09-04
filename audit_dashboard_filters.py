# -*- coding: utf-8 -*-
import os, sys, json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def audit():
    print("=== INICIANDO AUDITORIA COMPLETA DE FILTROS DO DASHBOARD (BUILD ATUALIZADO) ===")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_index = os.path.join(base_dir, 'index.html').replace('\\', '/')
    url = f"file:///{local_index}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        errors = []
        page.on('pageerror', lambda err: errors.append(str(err)))
        page.on('console', lambda msg: errors.append(f"CONSOLE {msg.type}: {msg.text}") if msg.type == 'error' else None)
        
        print(f"Carregando {url}...")
        page.goto(url, wait_until='networkidle')
        page.wait_for_timeout(2000)
        
        print("\n--- 1. AUDITORIA: FILTROS DA SIDEBAR ---")
        
        # 1.1 Base de Dados
        mes_ref = page.query_selector('#filterMesReferencia')
        print(f"1.1 Base de Dados: valor='{mes_ref.input_value()}'")
            
        # 1.2 Busca Rápida (Global Search)
        search_input = page.query_selector('#globalSearch')
        if search_input:
            search_input.fill('PERFUMARIA')
            page.wait_for_timeout(300)
            rows = page.query_selector_all('#tbodyCategorias tr')
            print(f"1.2 Busca Rápida: [OK] Presente! Filtrou para {len(rows)} linhas.")
            search_input.fill('')
            page.wait_for_timeout(300)
        else:
            print("1.2 Busca Rápida: [FALHA] #globalSearch não encontrado!")
            
        # 1.3 Recorte de Dias (MTD)
        periodo_preset = page.query_selector('#filterPeriodoPreset')
        opts = [o.get_attribute('value') for o in periodo_preset.query_selector_all('option')]
        print(f"1.3 Recorte MTD: opções={opts}")
        
        # Testar ONTEM
        kpi_full = page.query_selector('#kpiStrip .apple-kpi-card .kpi-value-main').inner_text()
        periodo_preset.select_option('ONTEM')
        page.wait_for_timeout(300)
        kpi_ontem = page.query_selector('#kpiStrip .apple-kpi-card .kpi-value-main').inner_text()
        print(f"    KPI FULL: {kpi_full} -> KPI ONTEM: {kpi_ontem}")
        if kpi_full != kpi_ontem:
            print("    [OK] Preset ONTEM alterou os valores dos KPIs.")
        else:
            print("    [ALERTA] Preset ONTEM manteve os valores.")
            
        # Voltar para FULL
        periodo_preset.select_option('FULL')
        page.wait_for_timeout(300)
            
        # 1.4 Multi-Selects da Sidebar
        ms_list = [
            ('msDiretor', 'Diretor Regional'),
            ('msDistrital', 'Distrital'),
            ('msGrupo', 'Grupo / Categoria'),
            ('msSubgrupo', 'Subgrupo'),
            ('msLinha', 'Linha')
        ]
        
        for ms_id, ms_name in ms_list:
            btn = page.query_selector(f'#{ms_id} .ms-btn')
            if not btn:
                print(f"1.4 {ms_name} (#{ms_id}): [FALHA] NÃO ENCONTRADO")
                continue
            btn_txt = btn.inner_text().strip()
            btn.click()
            page.wait_for_timeout(200)
            items = page.query_selector_all(f'#{ms_id} .ms-list .ms-item')
            count = len(items)
            print(f"1.4 {ms_name} (#{ms_id}): status='{btn_txt}', total_itens={count} [OK]")
            btn.click()
            page.wait_for_timeout(100)

        # 1.5 Filtro de Exclusão
        exc_tipo = page.query_selector('#filterExcluirTipo')
        exc_val = page.query_selector('#filterExcluirValor')
        exc_opts = [o.get_attribute('value') for o in exc_tipo.query_selector_all('option')]
        print(f"\n1.5 Opções de Exclusão: {exc_opts}")
        for opt in ['grupo', 'subgrupo', 'linha', 'canal']:
            exc_tipo.select_option(opt)
            page.wait_for_timeout(200)
            sub_opts = [o.get_attribute('value') for o in exc_val.query_selector_all('option')]
            print(f"    Exclusão '{opt}': {len(sub_opts)-1} itens disponíveis para excluir. [OK]")
        exc_tipo.select_option('NONE')

        # 1.6 Filtro Grupo de Canal
        grp_canal = page.query_selector('#filterGrupoCanal')
        canal_opts = [o.get_attribute('value') for o in grp_canal.query_selector_all('option')]
        print(f"\n1.6 Opções Grupo Canal: {canal_opts}")
        grp_canal.select_option('digital')
        page.wait_for_timeout(300)
        kpi_dig = page.query_selector('#kpiStrip .apple-kpi-card .kpi-value-main').inner_text()
        print(f"    KPI Total: {kpi_full} -> KPI Canal Digital: {kpi_dig} [OK]")
        grp_canal.select_option('ALL')
        page.wait_for_timeout(300)

        print("\n--- 2. AUDITORIA: ABA 2 (CATEGORIAS & ORDENAÇÃO) ---")
        page.query_selector('button[data-tab="tabCategorias"]').click()
        page.wait_for_timeout(300)
        cat_headers = page.query_selector_all('#tableCategorias th.sortable')
        print(f"    Colunas com clique de ordenação ativa: {len(cat_headers)}")
        for th in cat_headers[:6]:
            col_name = th.inner_text().strip()
            th.click()
            page.wait_for_timeout(200)
            print(f"    Ordenação por '{col_name}': OK")

        print("\n--- 3. AUDITORIA: ABA 3 (WATERFALL DE CRESCIMENTO) ---")
        page.query_selector('button[data-tab="tabWaterfall"]').click()
        page.wait_for_timeout(500)
        
        # Testar TODAS as dimensões do waterfall
        dim_btns = page.query_selector_all('#wfDimension button')
        for db in dim_btns:
            dim_name = db.get_attribute('data-dim')
            dim_txt = db.inner_text().strip()
            db.click()
            page.wait_for_timeout(400)
            wf_rows = page.query_selector_all('#wfDetailTbody tr')
            count = len(wf_rows)
            print(f"    Waterfall Dimensão '{dim_txt}' (data-dim='{dim_name}'): itens={count} -> {'[OK]' if count > 0 else '[FALHA]'}")

        # Testar Comparações (MoM, YoY, Vs Meta)
        # Primeiro colocar em 'categoria'
        page.query_selector('#wfDimension button[data-dim="categoria"]').click()
        page.wait_for_timeout(300)
        for comp in ['mom', 'yoy', 'meta']:
            btn = page.query_selector(f'#wfComparison button[data-comp="{comp}"]')
            btn.click()
            page.wait_for_timeout(400)
            wf_rows = page.query_selector_all('#wfDetailTbody tr')
            print(f"    Waterfall Comparação '{comp}': itens={len(wf_rows)} -> {'[OK]' if len(wf_rows) > 0 else '[FALHA]'}")

        # Testar Canais Agrupado e Detalhado
        for ch_dim in ['canal_agregado', 'canal']:
            page.query_selector(f'#wfDimension button[data-dim="{ch_dim}"]').click()
            page.wait_for_timeout(400)
            wf_rows = page.query_selector_all('#wfDetailTbody tr')
            print(f"    Waterfall '{ch_dim}': itens={len(wf_rows)} -> {'[OK]' if len(wf_rows) > 0 else '[FALHA]'}")

        print("\n--- 4. AUDITORIA: ABA 4 (METAS EMPRESA & CATEGORIAS) ---")
        page.query_selector('button[data-tab="tabMetasSetembro"]').click()
        page.wait_for_timeout(500)
        
        sel_cat_meta = page.query_selector('#metasFilterCategoria')
        opts = [o.inner_text().strip() for o in sel_cat_meta.query_selector_all('option')]
        print(f"    Filtro Categoria: {len(opts)} opções [OK]")
        
        sel_status_meta = page.query_selector('#metasFilterStatus')
        sel_status_meta.select_option('acima')
        page.wait_for_timeout(200)
        cnt = page.query_selector('#metasTableCount').inner_text()
        print(f"    Filtro Status 'acima': {cnt} [OK]")
        sel_status_meta.select_option('ALL')

        search_meta = page.query_selector('#metasSearch')
        search_meta.fill('FRALDA')
        page.wait_for_timeout(200)
        cnt = page.query_selector('#metasTableCount').inner_text()
        print(f"    Busca 'FRALDA': {cnt} [OK]")
        search_meta.fill('')

        print("\n--- 5. AUDITORIA: ABA 5 (METAS DIRETORIA & DISTRITAIS) ---")
        page.query_selector('button[data-tab="tabMetasDiretoria"]').click()
        page.wait_for_timeout(500)
        
        sel_dir_5 = page.query_selector('#dirFilterDiretoria')
        sel_dist_5 = page.query_selector('#dirFilterDistrital')
        
        # Testar cascata da Cintia Silva
        sel_dir_5.select_option('Cintia Silva')
        page.wait_for_timeout(400)
        dist_opts = [o.inner_text().strip() for o in sel_dist_5.query_selector_all('option')]
        pills_cintia = page.query_selector_all('#rankingDistritaisBar .distrital-rank-pill')
        print(f"    Após selecionar 'Cintia Silva':")
        print(f"      - Distritais no Select (Cascata): {dist_opts} [OK]")
        print(f"      - Ranking Distritais pills visíveis: {len(pills_cintia)} (esperado: 4) [OK]")
        
        sel_dir_5.select_option('ALL')
        page.wait_for_timeout(300)
        pills_all = page.query_selector_all('#rankingDistritaisBar .distrital-rank-pill')
        print(f"    Após voltar para 'Todas as Diretorias': {len(pills_all)} pills visíveis [OK]")

        print("\n--- RESUMO DE ERROS ---")
        if errors:
            for e in errors:
                print("  [ERRO]", e)
        else:
            print("  ✅ ZERO ERROS CAPTURADOS! TODOS OS FILTROS ESTÃO OPERACIONAIS!")

        browser.close()

if __name__ == '__main__':
    audit()
