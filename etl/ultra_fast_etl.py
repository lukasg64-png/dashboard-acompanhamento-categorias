"""
ultra_fast_etl.py — On-the-fly streaming aggregator for BASE DADOS.xlsx.
Aggregates 1M+ rows into ~30k key combinations during XML parsing.
Instant execution speed (~5-10 seconds total).
"""
import os, sys, time, tempfile, zipfile
import xml.parsers.expat
import pandas as pd
from collections import defaultdict

tmp = os.path.join(tempfile.gettempdir(), 'BASE_DADOS_temp.xlsx')

def col2num(col_str):
    num = 0
    for c in col_str:
        num = num * 26 + (ord(c) - ord('A') + 1)
    return num - 1

def run_ultra_fast_etl():
    t0 = time.time()
    print("=" * 70)
    print("INICIANDO ULTRA FAST ETL (On-the-fly streaming aggregator)")
    print("=" * 70)
    
    zf = zipfile.ZipFile(tmp, 'r')
    
    # 1. Read shared strings
    t1 = time.time()
    shared_strings = []
    if 'xl/sharedStrings.xml' in zf.namelist():
        current_text = []
        in_t = False
        def start_elem(name, attrs):
            nonlocal in_t
            if name == 't': in_t = True
        def end_elem(name):
            nonlocal in_t
            if name == 't':
                in_t = False
                shared_strings.append("".join(current_text))
                current_text.clear()
        def char_data(data):
            if in_t: current_text.append(data)
        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = start_elem
        p.EndElementHandler = end_elem
        p.CharacterDataHandler = char_data
        with zf.open('xl/sharedStrings.xml') as f:
            p.ParseFile(f)
    print(f"[OK] Shared strings: {len(shared_strings):,} itens em {time.time() - t1:.2f}s")
    
    # Define column sets
    jul_25_cols = set(range(9, 71, 2))   # Jul/25
    jun_26_cols = set(range(71, 131, 2))  # Jun/26
    jul_26_cols = set(range(131, 193, 2)) # Jul/26
    
    # Aggregator dictionary: key -> [v_jul_25, v_jun_26, v_jul_26]
    # Key: (diretor, distrital, grupo, subgrupo, linha, laboratorio, canal)
    agg = defaultdict(lambda: [0.0, 0.0, 0.0])
    
    current_row_num = 0
    current_cells = {}
    cell_ref = ''
    cell_type = ''
    val_buf = []
    row_count = 0
    
    t2 = time.time()
    print("Lendo e agregando sheet1.xml em tempo de execução...")

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
            if current_row_num >= 3: # Data rows
                row_count += 1
                
                # Extract dimensions
                grupo = current_cells.get(0, '').strip()
                subgrupo = current_cells.get(1, '').strip()
                agrupamento = current_cells.get(2, '').strip()
                linha = current_cells.get(3, '').strip()
                laboratorio = current_cells.get(4, '').strip()
                produto = current_cells.get(5, '').strip()
                diretor = current_cells.get(6, '').strip()
                distrital = current_cells.get(7, '').strip()
                canal = current_cells.get(8, '').strip()
                
                v_jul_25 = 0.0
                v_jun_26 = 0.0
                v_jul_26 = 0.0
                
                for c_idx, raw_v in current_cells.items():
                    if not raw_v or raw_v == '-':
                        continue
                    try:
                        f_v = float(raw_v)
                    except ValueError:
                        continue
                    
                    if c_idx in jul_25_cols:
                        v_jul_25 += f_v
                    elif c_idx in jun_26_cols:
                        v_jun_26 += f_v
                    elif c_idx in jul_26_cols:
                        v_jul_26 += f_v

                if v_jul_25 != 0 or v_jun_26 != 0 or v_jul_26 != 0:
                    key = (diretor, distrital, grupo, subgrupo, linha, laboratorio, produto, canal)
                    tot = agg[key]
                    tot[0] += v_jul_25
                    tot[1] += v_jun_26
                    tot[2] += v_jul_26

    def char_data(data):
        val_buf.append(data)

    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data
    
    with zf.open('xl/worksheets/sheet1.xml') as f:
        p.ParseFile(f)
        
    zf.close()
    
    print(f"[OK] {row_count:,} linhas processadas em {time.time() - t2:.2f}s!")
    print(f"[OK] {len(agg):,} combinações únicas agregadas em memória!")
    
    # Build DataFrame from aggregated dict
    rows = []
    for (diretor, distrital, grupo, subgrupo, linha, laboratorio, produto, canal), (v25, v26_06, v26_07) in agg.items():
        rows.append({
            'diretor': diretor,
            'distrital': distrital,
            'grupo': grupo,
            'subgrupo': subgrupo,
            'linha': linha,
            'laboratorio': laboratorio,
            'produto': produto,
            'canal': canal,
            'venda_jul_25': round(v25, 2),
            'venda_jun_26': round(v26_06, 2),
            'venda_jul_26': round(v26_07, 2)
        })
        
    df = pd.DataFrame(rows)
    print(f"[OK] DataFrame final gerado! Shape: {df.shape}")
    print(f"     Total Jul/26: R$ {df['venda_jul_26'].sum():,.2f}")
    print(f"     Total Jun/26: R$ {df['venda_jun_26'].sum():,.2f}")
    print(f"     Total Jul/25: R$ {df['venda_jul_25'].sum():,.2f}")
    print(f"     Tempo total: {time.time() - t0:.2f}s")
    
    # Save parquet cache
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    os.makedirs(cache_dir, exist_ok=True)
    parquet_path = os.path.join(cache_dir, 'base_dados_summary.parquet')
    df.to_parquet(parquet_path, index=False)
    print(f"[OK] Cache Parquet salvo: {parquet_path} ({os.path.getsize(parquet_path)/(1024*1024):.2f} MB)")
    
    return df

if __name__ == '__main__':
    run_ultra_fast_etl()
