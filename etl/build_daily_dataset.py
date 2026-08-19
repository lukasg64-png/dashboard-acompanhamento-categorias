"""
build_daily_dataset.py — Reads BASE DADOS.xlsx and outputs daily sales array
for each category and hierarchy level.
"""
import os, sys, time, tempfile, zipfile, json
import xml.parsers.expat
import pandas as pd
import numpy as np

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

    # 2. Header date mapping
    header_cells = {}
    cell_ref = ''
    cell_type = ''
    val_buf = []
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
        p.Parse(f.read(500000), False)

    date_cols = []
    for c_idx in range(9, 193, 2):
        d_str = header_cells.get(c_idx, '')
        if d_str:
            # Parse 'DD/MM/YYYY'
            parts = d_str.split('/')
            if len(parts) == 3:
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                date_cols.append((c_idx, d_str, day, month, year))

    # Sort date_cols chronologically
    date_cols.sort(key=lambda x: (x[4], x[3], x[2]))
    dates_header = [x[1] for x in date_cols]
    col_to_date_idx = {x[0]: i for i, x in enumerate(date_cols)}
    num_dates = len(date_cols)

    print(f"Total date columns mapped: {num_dates}")
    print("Dates header order:", dates_header[:3], "...", dates_header[-3:])

    # 3. Stream data and aggregate by (diretor, distrital, grupo, linha, canal) -> 92 daily totals
    from collections import defaultdict
    # key -> np.zeros(num_dates)
    agg = defaultdict(lambda: np.zeros(num_dates, dtype=np.float64))

    current_row_num = 0
    current_cells = {}
    row_count = 0

    def start_elem(name, attrs):
        nonlocal cell_ref, cell_type, val_buf, current_row_num
        if name == 'row':
            current_row_num = int(attrs.get('r', '0'))
            current_cells.clear()
        elif name == 'c':
            cell_ref = attrs.get('r', '')
            cell_type = attrs.get('t', '')
            val_buf = []

    def end_elem(name):
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
            if current_row_num >= 3:
                row_count += 1
                grupo = current_cells.get(0, '').strip()
                subgrupo = current_cells.get(1, '').strip()
                linha = current_cells.get(3, '').strip()
                laboratorio = current_cells.get(4, '').strip()
                diretor = current_cells.get(6, '').strip()
                distrital = current_cells.get(7, '').strip()
                canal = current_cells.get(8, '').strip()

                key = (diretor, distrital, grupo, subgrupo, linha, laboratorio, canal)
                
                for c_idx, d_idx in col_to_date_idx.items():
                    raw_v = current_cells.get(c_idx, '')
                    if raw_v and raw_v != '-':
                        try:
                            agg[key][d_idx] += float(raw_v)
                        except ValueError:
                            pass

    def char_data(data): val_buf.append(data)

    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = start_elem
    p.EndElementHandler = end_elem
    p.CharacterDataHandler = char_data
    with zf.open('xl/worksheets/sheet1.xml') as f:
        p.ParseFile(f)
    zf.close()

    print(f"Processed {row_count:,} rows in {time.time() - t0:.2f}s!")
    print(f"Aggregated {len(agg):,} unique key combinations.")

    # Save to parquet
    records = []
    for (diretor, distrital, grupo, subgrupo, linha, laboratorio, canal), daily_arr in agg.items():
        rec = {
            'diretor': diretor,
            'distrital': distrital,
            'grupo': grupo,
            'subgrupo': subgrupo,
            'linha': linha,
            'laboratorio': laboratorio,
            'canal': canal
        }
        for d_idx, d_str in enumerate(dates_header):
            rec[d_str] = round(float(daily_arr[d_idx]), 2)
        records.append(rec)

    df_daily = pd.DataFrame(records)
    print("Daily DataFrame shape:", df_daily.shape)
    
    parquet_daily = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'base_dados_daily.parquet')
    df_daily.to_parquet(parquet_daily, index=False)
    print(f"Saved daily parquet cache: {parquet_daily} ({os.path.getsize(parquet_daily)/(1024*1024):.2f} MB)")

if __name__ == '__main__':
    run()
