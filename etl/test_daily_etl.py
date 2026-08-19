"""
test_daily_etl.py — Aggregates daily sales per date for each hierarchy row.
Evaluates file size and speed.
"""
import os, sys, time, tempfile, zipfile
import xml.parsers.expat
import pandas as pd
import json

tmp = os.path.join(tempfile.gettempdir(), 'BASE_DADOS_temp.xlsx')

def col2num(col_str):
    num = 0
    for c in col_str:
        num = num * 26 + (ord(c) - ord('A') + 1)
    return num - 1

def run():
    t0 = time.time()
    zf = zipfile.ZipFile(tmp, 'r')
    
    # 1. Read shared strings
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
            
    # Parse header row 1 to get exact date per column index
    # We want cols 9..192 step 2 (Resultado Líquido for each date)
    date_col_map = {} # col_idx -> date_str (e.g. '01/07/2025')
    
    cell_ref = ''
    cell_type = ''
    val_buf = []
    header_cells = {}
    
    def start_elem(name, attrs):
        nonlocal cell_ref, cell_type, val_buf
        if name == 'c':
            cell_ref = attrs.get('r', '')
            cell_type = attrs.get('t', '')
            val_buf = []
    def end_elem(name):
        if name == 'c':
            col_letter = "".join([c for c in cell_ref if c.isalpha()])
            row_num = int("".join([c for c in cell_ref if c.isdigit()]))
            if row_num == 1:
                c_idx = col2num(col_letter)
                raw_val = "".join(val_buf).strip()
                if cell_type == 's' and raw_val.isdigit():
                    idx = int(raw_val)
                    val = shared_strings[idx] if idx < len(shared_strings) else raw_val
                else:
                    val = raw_val
                header_cells[c_idx] = val
    def char_data(data): val_buf.append(data)
    
    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = start_elem
    p.EndElementHandler = end_elem
    p.CharacterDataHandler = char_data
    
    with zf.open('xl/worksheets/sheet1.xml') as f:
        # read first 500k bytes for row 1
        p.Parse(f.read(500000), False)

    for c_idx in range(9, 193, 2):
        d_str = header_cells.get(c_idx, '')
        if d_str:
            date_col_map[c_idx] = d_str

    print(f"Total mapped date columns: {len(date_col_map)}")
    dates_list = sorted(list(set(date_col_map.values())))
    print(f"Unique dates ({len(dates_list)}): {dates_list[:5]} ... {dates_list[-5:]}")

if __name__ == '__main__':
    run()
