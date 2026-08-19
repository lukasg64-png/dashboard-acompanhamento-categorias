"""
fast_etl_test.py — Fast streaming ETL that processes sheet1.xml row by row,
aggregates daily columns into period totals (Jul/25, Jun/26, Jul/26),
and saves intermediate Parquet.
"""
import os, sys, time, tempfile, zipfile
import xml.parsers.expat
import pandas as pd
import numpy as np

tmp = os.path.join(tempfile.gettempdir(), 'BASE_DADOS_temp.xlsx')

def col2num(col_str):
    num = 0
    for c in col_str:
        num = num * 26 + (ord(c) - ord('A') + 1)
    return num - 1

def process_base_dados_fast():
    t0 = time.time()
    print("Iniciando leitura ultra-rápida do XLSX...")
    
    zf = zipfile.ZipFile(tmp, 'r')
    
    # 1. Read shared strings
    print("Lendo sharedStrings.xml...")
    t1 = time.time()
    shared_strings = []
    if 'xl/sharedStrings.xml' in zf.namelist():
        current_text = []
        in_t = False
        def start_element(name, attrs):
            nonlocal in_t
            if name == 't': in_t = True
        def end_element(name):
            nonlocal in_t
            if name == 't':
                in_t = False
                shared_strings.append("".join(current_text))
                current_text.clear()
        def char_data(data):
            if in_t: current_text.append(data)
        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = start_element
        p.EndElementHandler = end_element
        p.CharacterDataHandler = char_data
        with zf.open('xl/sharedStrings.xml') as f:
            p.ParseFile(f)
    print(f"Shared strings carregadas ({len(shared_strings)} itens) em {time.time() - t1:.2f}s")
    
    # Define column index sets for periods
    # Cols 0..8 are dimensional:
    # 0: Desc_Grupo, 1: Desc_Subgrupo, 2: Agrupamento, 3: Desc_Linha, 4: Laboratorio, 5: Desc_Produto, 6: Diretor, 7: Distrital, 8: Canal
    # Jul/25: cols 9, 11, 13, ..., 69 (step 2)
    jul_25_cols = set(range(9, 71, 2))
    # Jun/26: cols 71, 73, 75, ..., 129 (step 2)
    jun_26_cols = set(range(71, 131, 2))
    # Jul/26: cols 131, 133, 135, ..., 191 (step 2)
    jul_26_cols = set(range(131, 193, 2))
    
    print("Processando sheet1.xml (linha por linha)...")
    t2 = time.time()
    
    records = []
    
    current_row_num = 0
    current_cells = {}
    cell_ref = ''
    cell_type = ''
    val_buf = []
    
    row_count = 0
    
    def start_element(name, attrs):
        nonlocal cell_ref, cell_type, val_buf, current_row_num
        if name == 'row':
            current_row_num = int(attrs.get('r', '0'))
            current_cells.clear()
        elif name == 'c':
            cell_ref = attrs.get('r', '')
            cell_type = attrs.get('t', '')
            val_buf = []

    def end_element(name):
        nonlocal current_row_num, row_count
        if name == 'c':
            col_letter = "".join([c for c in cell_ref if c.isalpha()])
            c_idx = col2num(col_letter)
            raw_val = "".join(val_buf).strip()
            
            if cell_type == 's' and raw_val.isdigit():
                idx = int(raw_val)
                val = shared_strings[idx] if idx < len(shared_strings) else raw_val
            else:
                val = raw_val
            
            current_cells[c_idx] = val

        elif name == 'row':
            if current_row_num >= 3: # Row 3+ is data
                row_count += 1
                
                # Extract dimensions
                grupo = current_cells.get(0, '')
                subgrupo = current_cells.get(1, '')
                agrupamento = current_cells.get(2, '')
                linha = current_cells.get(3, '')
                laboratorio = current_cells.get(4, '')
                produto = current_cells.get(5, '')
                diretor = current_cells.get(6, '')
                distrital = current_cells.get(7, '')
                canal = current_cells.get(8, '')
                
                # Sum period sales
                v_jul_25 = 0.0
                v_jun_26 = 0.0
                v_jul_26 = 0.0
                
                for c_idx, raw_v in current_cells.items():
                    if c_idx in jul_25_cols:
                        if raw_v and raw_v != '-':
                            try: v_jul_25 += float(raw_v)
                            except ValueError: pass
                    elif c_idx in jun_26_cols:
                        if raw_v and raw_v != '-':
                            try: v_jun_26 += float(raw_v)
                            except ValueError: pass
                    elif c_idx in jul_26_cols:
                        if raw_v and raw_v != '-':
                            try: v_jul_26 += float(raw_v)
                            except ValueError: pass

                records.append({
                    'grupo': grupo,
                    'subgrupo': subgrupo,
                    'agrupamento': agrupamento,
                    'linha': linha,
                    'laboratorio': laboratorio,
                    'produto': produto,
                    'diretor': diretor,
                    'distrital': distrital,
                    'canal': canal,
                    'venda_jul_25': v_jul_25,
                    'venda_jun_26': v_jun_26,
                    'venda_jul_26': v_jul_26
                })
                
                if row_count % 100000 == 0:
                    print(f"  Processadas {row_count:,} linhas... ({time.time() - t2:.1f}s)")

    def char_data(data):
        val_buf.append(data)

    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data
    
    with zf.open('xl/worksheets/sheet1.xml') as f:
        p.ParseFile(f)
        
    zf.close()
    
    print(f"Total de {row_count:,} linhas processadas em {time.time() - t2:.2f}s!")
    
    df = pd.DataFrame(records)
    print(f"DataFrame criado! Shape: {df.shape}")
    print(f"Total venda Jul/26: R$ {df['venda_jul_26'].sum():,.2f}")
    print(f"Total venda Jun/26: R$ {df['venda_jun_26'].sum():,.2f}")
    print(f"Total venda Jul/25: R$ {df['venda_jul_25'].sum():,.2f}")
    
    parquet_path = os.path.join(tempfile.gettempdir(), 'base_dados_summary.parquet')
    df.to_parquet(parquet_path, index=False)
    print(f"Parquet salvo em {parquet_path} ({os.path.getsize(parquet_path)/(1024*1024):.2f} MB)")
    return df

if __name__ == '__main__':
    process_base_dados_fast()
