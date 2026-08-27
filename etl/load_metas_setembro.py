"""
load_metas_setembro.py — Processa o Excel de metas de Setembro/2026.
Lê as 598 linhas com meta comercial alocada e a curva diária com % por dia.
Gera JSONs com metas rateadas por linha × dia para alimentar o dashboard.
"""
import os, sys, json, shutil
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

import openpyxl

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'setembro')
EXCEL_ORIGINAL = os.path.join(BASE_DIR, 'metas setembro.xlsx')
EXCEL_COPIA = os.path.join(BASE_DIR, 'metas_setembro_copia.xlsx')

def get_excel_path():
    """Tenta abrir o original; se estiver travado (aberto no Excel), usa cópia existente."""
    # 1. Tenta o original
    try:
        with open(EXCEL_ORIGINAL, 'rb') as f:
            f.read(1)
        return EXCEL_ORIGINAL
    except PermissionError:
        pass
    
    # 2. Tenta cópia existente
    if os.path.exists(EXCEL_COPIA):
        print("  ⚠️ Excel original travado, usando cópia existente...")
        return EXCEL_COPIA
    
    # 3. Tenta via cmd copy (bypass lock)
    print("  ⚠️ Excel original travado, tentando criar cópia via cmd...")
    import subprocess
    try:
        subprocess.run(f'copy "{EXCEL_ORIGINAL}" "{EXCEL_COPIA}"', shell=True, check=True,
                       capture_output=True, cwd=BASE_DIR)
        return EXCEL_COPIA
    except Exception:
        pass
    
    raise FileNotFoundError(f"Não foi possível acessar o Excel de metas: {EXCEL_ORIGINAL}")

def load_linhas(wb):
    """Lê aba '1. Modelo por linha' — 598 linhas com meta mensal."""
    ws = wb[wb.sheetnames[0]]  # "1. Modelo por linha"
    linhas = []
    for row_idx in range(5, ws.max_row + 1):  # Dados começam na row 5
        linha_nome = ws.cell(row_idx, 1).value
        familia = ws.cell(row_idx, 2).value
        categoria = ws.cell(row_idx, 3).value
        meta_mensal = ws.cell(row_idx, 4).value
        
        if linha_nome is None:
            continue
        # Parar ao chegar nas linhas de totalização
        nome_str = str(linha_nome).strip()
        if nome_str.startswith('SOMA DA TABELA') or nome_str.startswith('≡') or nome_str.startswith('='):
            break
        
        meta_val = float(meta_mensal) if meta_mensal is not None else 0.0
        
        linhas.append({
            'linha': nome_str,
            'familia': str(familia).strip() if familia else '',
            'categoria': str(categoria).strip() if categoria else '',
            'meta_mensal': round(meta_val, 2)
        })
    
    return linhas

def load_curva_diaria(wb):
    """Lê aba '3. Curva diária set26' — 30 dias com pesos e percentuais."""
    # Procurar aba pela posição (index 2) ou nome parcial
    target_sheet = None
    for sn in wb.sheetnames:
        if 'curva' in sn.lower() or 'di' in sn.lower():
            target_sheet = sn
            break
    if not target_sheet:
        target_sheet = wb.sheetnames[2]  # Fallback: terceira aba
    
    ws = wb[target_sheet]
    dias = []
    for row_idx in range(5, 35):  # Rows 5-34 = dias 1-30
        dia_num = ws.cell(row_idx, 1).value
        dia_semana = ws.cell(row_idx, 2).value
        peso = ws.cell(row_idx, 3).value
        pct_dia = ws.cell(row_idx, 4).value
        pct_acum = ws.cell(row_idx, 5).value
        proj_dia = ws.cell(row_idx, 6).value
        proj_acum = ws.cell(row_idx, 7).value
        meta_dia = ws.cell(row_idx, 8).value  # Meta +16% Dia R$
        meta_acum = ws.cell(row_idx, 9).value  # Meta +16% Acum. R$
        
        if dia_num is None:
            continue
        
        dias.append({
            'dia': int(dia_num),
            'dia_semana': str(dia_semana).strip() if dia_semana else '',
            'peso': round(float(peso), 8) if peso else 0,
            'pct_dia': round(float(pct_dia), 10) if pct_dia else 0,
            'pct_acum': round(float(pct_acum), 10) if pct_acum else 0,
            'proj_dia': round(float(proj_dia), 2) if proj_dia else 0,
            'proj_acum': round(float(proj_acum), 2) if proj_acum else 0,
            'meta_dia': round(float(meta_dia), 2) if meta_dia else 0,
            'meta_acum': round(float(meta_acum), 2) if meta_acum else 0,
        })
    
    return dias

def ratear_metas_por_dia(linhas, curva):
    """Distribui a meta mensal de cada linha pelos 30 dias usando % da curva."""
    pct_dias = [d['pct_dia'] for d in curva]
    
    for item in linhas:
        meta_m = item['meta_mensal']
        item['meta_diaria'] = [round(meta_m * pct, 2) for pct in pct_dias]
        # Meta acumulada por dia
        acum = 0
        meta_acum = []
        for v in item['meta_diaria']:
            acum += v
            meta_acum.append(round(acum, 2))
        item['meta_acum'] = meta_acum
    
    return linhas

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print("\n" + "=" * 60)
    print("  PROCESSANDO EXCEL DE METAS — SETEMBRO/2026")
    print("=" * 60)
    
    excel_path = get_excel_path()
    print(f"  📂 Lendo: {os.path.basename(excel_path)}")
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    
    # 1. Ler linhas com meta mensal
    linhas = load_linhas(wb)
    print(f"  📊 {len(linhas)} linhas de produto carregadas")
    
    # 2. Ler curva diária
    curva = load_curva_diaria(wb)
    print(f"  📅 {len(curva)} dias na curva diária")
    
    # 3. Validar total
    total_metas = sum(l['meta_mensal'] for l in linhas)
    pct_total = sum(d['pct_dia'] for d in curva)
    meta_empresa_mes = curva[-1]['meta_acum'] if curva else 0
    print(f"  💰 Soma das metas por linha: R$ {total_metas:,.2f}")
    print(f"  📐 Soma dos % diários: {pct_total:.6f} (esperado: 1.0)")
    print(f"  🏢 Meta empresa mês (curva): R$ {meta_empresa_mes:,.2f}")
    
    # 4. Ratear metas por dia
    linhas = ratear_metas_por_dia(linhas, curva)
    
    # 5. Enriquecer com grupo/subgrupo via hierarquia do dashboard principal
    hier_paths = [
        os.path.join(BASE_DIR, 'data', 'agosto', 'hierarquia_detalhada.json'),
        os.path.join(BASE_DIR, 'data', 'hierarquia_detalhada.json'),
    ]
    mapping = {}
    for hp in hier_paths:
        if os.path.exists(hp):
            with open(hp, 'r', encoding='utf-8') as f:
                hier = json.load(f)
            for h in hier:
                ln = h.get('linha', '')
                if ln and ln not in mapping:
                    # Limpar sufixo numérico dos nomes tipo "Medicamentos(1)"
                    grupo_raw = h.get('grupo', '')
                    subgrupo_raw = h.get('subgrupo', '')
                    import re
                    grupo_clean = re.sub(r'\(\d+\)$', '', grupo_raw).strip()
                    subgrupo_clean = re.sub(r'\(\d+\)$', '', subgrupo_raw).strip()
                    mapping[ln] = {'grupo': grupo_clean, 'subgrupo': subgrupo_clean}
            print(f"  🗂️ Mapeamento grupo/subgrupo: {len(mapping)} linhas de {os.path.basename(hp)}")
            break
    
    # Intelligent manual mapping for the 31 lines not in hierarquia_detalhada
    manual_map = {
        'SEM LINHA': ('Diversos', 'Sem Linha'),
        'IMUNOLOGIA': ('Medicamentos', 'Imunologia'),
        'ANTI-RETROVIRAIS (HIV/HEPATITE)': ('Medicamentos', 'Anti-Infecciosos'),
        'OTC- DISFUNCAO ERETIL': ('Medicamentos', 'OTC'),
        'ANTICORPOS MONOCLONAIS': ('Medicamentos', 'Especiais'),
        'GLICOCORTICOIDES': ('Medicamentos', 'Anti-Inflamatórios'),
        'MATERIAL DE ESCRITORIO': ('Diversos', 'Consumo e Materiais'),
        'CD CONSTRUÇÃO': ('Diversos', 'Consumo e Materiais'),
        'MATERIAIS INFORMATICA': ('Diversos', 'Consumo e Materiais'),
        'IMOBILIZADO': ('Diversos', 'Consumo e Materiais'),
        'USO E CONSUMO': ('Diversos', 'Consumo e Materiais'),
        'COLORACAO': ('Perfumaria', 'Coloração'),
        'ACESSORIOS - INFANTIL SEGURANÇA': ('Perfumaria', 'Acessórios'),
        'DESODORANTE - AERO UNISSEX PACK': ('Perfumaria', 'Desodorantes'),
        'DESODORANTE - SPRAY FEMININO': ('Perfumaria', 'Desodorantes'),
        'MAQUIAGEM - DISPLAY': ('Perfumaria', 'Maquiagem'),
        'MAQUIAGEM - SOMBRA LIQUIDA': ('Perfumaria', 'Maquiagem'),
        'BANDEJA - MAQUIAGEM': ('Perfumaria', 'Maquiagem'),
        'MAQUIAGEM - DELINADOR EM GEL': ('Perfumaria', 'Maquiagem'),
        'CAPILAR - FINALIZADORES': ('Perfumaria', 'Capilar'),
        'KIT - CAPILAR MASSIVO': ('Perfumaria', 'Capilar'),
        'CAPILAR - BASICO': ('Perfumaria', 'Capilar'),
        'CAPILAR - MASSIVO': ('Perfumaria', 'Capilar'),
        'DERMO - MAQUIAGEM': ('Dermo-Cosmeticos', 'Maquiagem'),
        'ANTIOXIDANTE': ('Dermo-Cosmeticos', 'Tratamento'),
        'HOME CARE': ('Conveniencia', 'Home Care'),
        'HOME CARE - ALCOOL': ('Conveniencia', 'Home Care'),
        'ERVA MATE': ('Conveniencia', 'Alimentos'),
        'ALIMENTARES': ('Conveniencia', 'Alimentos'),
        'REFRIGERADOS': ('Conveniencia', 'Bebidas e Refrigerados'),
        'CHICLETES E BALAS': ('Conveniencia', 'Bomboniere'),
    }

    mapped = 0
    for item in linhas:
        ln = item['linha'].strip()
        if ln in manual_map:
            item['grupo'], item['subgrupo'] = manual_map[ln]
            mapped += 1
        elif ln in mapping:
            item['grupo'] = mapping[ln]['grupo']
            item['subgrupo'] = mapping[ln]['subgrupo']
            mapped += 1
        else:
            # Fallback inteligente
            cat = item.get('categoria', 'Outros')
            item['grupo'] = 'Medicamentos' if 'MED' in cat.upper() else 'Perfumaria'
            item['subgrupo'] = item.get('familia', 'Outros')

    print(f"  📋 {mapped}/{len(linhas)} linhas mapeadas para grupo/subgrupo (100% com grupo definido)")
    
    # 6. Validar rateio
    sample = linhas[0]
    soma_rateio = sum(sample['meta_diaria'])
    print(f"  ✅ Validação rateio '{sample['linha']}': Meta={sample['meta_mensal']:,.2f} Soma_dias={soma_rateio:,.2f} (diff={abs(sample['meta_mensal']-soma_rateio):,.2f})")
    
    # 6. Salvar JSONs
    # 6a. Metas por linha × dia
    out_metas = os.path.join(DATA_DIR, 'metas_por_linha_dia.json')
    with open(out_metas, 'w', encoding='utf-8') as f:
        json.dump(linhas, f, ensure_ascii=False, indent=2)
    print(f"  💾 {out_metas}")
    
    # 6b. Curva diária empresa
    out_curva = os.path.join(DATA_DIR, 'curva_diaria.json')
    with open(out_curva, 'w', encoding='utf-8') as f:
        json.dump(curva, f, ensure_ascii=False, indent=2)
    print(f"  💾 {out_curva}")
    
    # 6c. Resumo executivo
    resumo = {
        'mes': 'Setembro/2026',
        'dias_totais': len(curva),
        'total_linhas': len(linhas),
        'meta_empresa_mensal': round(total_metas, 2),
        'meta_empresa_curva': meta_empresa_mes,
        'categorias': {
            'Medicamento': len([l for l in linhas if l['categoria'] == 'Medicamento']),
            'Não-Medicamento': len([l for l in linhas if l['categoria'] != 'Medicamento']),
        },
        'top10_linhas': [
            {'linha': l['linha'], 'meta': l['meta_mensal']}
            for l in sorted(linhas, key=lambda x: x['meta_mensal'], reverse=True)[:10]
        ]
    }
    out_resumo = os.path.join(DATA_DIR, 'resumo_metas.json')
    with open(out_resumo, 'w', encoding='utf-8') as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    print(f"  💾 {out_resumo}")
    
    wb.close()
    print(f"\n  🎉 Processamento concluído! {len(linhas)} linhas × {len(curva)} dias = {len(linhas)*len(curva)} células de meta.")
    
    return linhas, curva

if __name__ == '__main__':
    main()
