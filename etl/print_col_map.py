"""Print full column mapping from header_data."""
import os, sys, tempfile, zipfile
from fast_excel_reader import parse_shared_strings, parse_sheet_header

tmp = os.path.join(tempfile.gettempdir(), 'BASE_DADOS_temp.xlsx')

with zipfile.ZipFile(tmp, 'r') as zf:
    shared_strings = parse_shared_strings(zf)
    header_data = parse_sheet_header(zf, shared_strings)

row1 = header_data[1] # Dates
row2 = header_data[2] # Metric names ('Desc_Grupo', ..., 'Canal', 'Resultado Líquido', 'Valor Desconto', ...)

print("Total columns in Row 1:", len(row1))
print("Total columns in Row 2:", len(row2))

# Map columns
col_map = []
for idx in sorted(row2.keys()):
    date_val = row1.get(idx, '')
    metric_val = row2.get(idx, '')
    col_map.append((idx, metric_val, date_val))
    print(f"Col {idx:3d}: metric={metric_val!r:25s} date={date_val!r}")
