"""
fast_excel_reader.py — High-speed streaming parser for large XLSX files.
Uses zipfile + xml.parsers.expat + sharedStrings.xml.
Converts Excel daily columns directly into aggregated monthly metrics.
"""
import os, sys, time, tempfile, zipfile
import xml.parsers.expat
import pandas as pd
import numpy as np

tmp = os.path.join(tempfile.gettempdir(), 'BASE_DADOS_temp.xlsx')
src = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\Acompanhamento Categorias\BASE DADOS.xlsx"
if os.path.exists(src):
    import shutil
    try:
        shutil.copy2(src, tmp)
    except Exception as e:
        print("Copy error:", e)

def parse_shared_strings(zf):
    """Read sharedStrings.xml if present."""
    strings = []
    if 'xl/sharedStrings.xml' not in zf.namelist():
        return strings
    
    current_text = []
    in_t = False
    
    def start_element(name, attrs):
        nonlocal in_t
        if name == 't':
            in_t = True

    def end_element(name):
        nonlocal in_t
        if name == 't':
            in_t = False
            strings.append("".join(current_text))
            current_text.clear()

    def char_data(data):
        if in_t:
            current_text.append(data)

    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data
    
    with zf.open('xl/sharedStrings.xml') as f:
        p.ParseFile(f)
    
    return strings

def parse_sheet_header(zf, shared_strings):
    """Parse first 2 rows of sheet1.xml to get column mapping and date ranges."""
    sheet_name = 'xl/worksheets/sheet1.xml'
    
    row_idx = 0
    col_idx = 0
    cell_ref = ''
    cell_type = ''
    val_buf = []
    
    rows_data = {}
    
    def col2num(col_str):
        num = 0
        for c in col_str:
            num = num * 26 + (ord(c) - ord('A') + 1)
        return num - 1

    def start_element(name, attrs):
        nonlocal cell_ref, cell_type, val_buf
        if name == 'c':
            cell_ref = attrs.get('r', '')
            cell_type = attrs.get('t', '')
            val_buf = []

    def end_element(name):
        nonlocal row_idx
        if name == 'c':
            col_letter = "".join([c for c in cell_ref if c.isalpha()])
            row_num = int("".join([c for c in cell_ref if c.isdigit()]))
            
            if row_num <= 3:
                c_idx = col2num(col_letter)
                raw_val = "".join(val_buf).strip()
                if cell_type == 's' and raw_val.isdigit():
                    idx = int(raw_val)
                    val = shared_strings[idx] if idx < len(shared_strings) else raw_val
                else:
                    val = raw_val
                
                if row_num not in rows_data:
                    rows_data[row_num] = {}
                rows_data[row_num][c_idx] = val

    def char_data(data):
        val_buf.append(data)

    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data
    
    with zf.open(sheet_name) as f:
        # Read first 1MB to get header rows quickly
        chunk = f.read(500000)
        try:
            p.Parse(chunk, False)
        except Exception:
            pass

    return rows_data

t0 = time.time()
print("Opening zip file...")
with zipfile.ZipFile(tmp, 'r') as zf:
    print(f"Zip opened in {time.time() - t0:.2f}s")
    t1 = time.time()
    shared_strings = parse_shared_strings(zf)
    print(f"Shared strings loaded: {len(shared_strings)} items in {time.time() - t1:.2f}s")
    
    t2 = time.time()
    header_data = parse_sheet_header(zf, shared_strings)
    print(f"Header parsed in {time.time() - t2:.2f}s")

for r in sorted(header_data.keys()):
    items = sorted(header_data[r].items())[:20]
    print(f"Row {r}: {items}")
