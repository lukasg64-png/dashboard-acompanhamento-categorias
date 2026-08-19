"""
test_size_reduction.py — Test size reduction techniques to get dist/index.html under 9 MB
"""
import os, json

DATA_DIR = r"c:\Users\lucas.alves6\OneDrive - Farmácias São João\Documentos\ANTIGRAVITI\dashboard-acompanhamento-categorias\data"
hier_path = os.path.join(DATA_DIR, 'hierarquia_detalhada.json')

with open(hier_path, 'r', encoding='utf-8') as f:
    records = json.load(f)

print(f"Original record count in hierarquia_detalhada.json: {len(records)}")

# Test compact rounding
def compact_arr(arr):
    return [round(x, 1) if x != 0 else 0 for x in arr]

for r in records:
    for k in ['d25', 'd26_06', 'd26_07', 'dig_d25', 'dig_d26_06', 'dig_d26_07', 'dt_d25', 'dt_d26_06', 'dt_d26_07']:
        if k in r:
            r[k] = compact_arr(r[k])

s = json.dumps(records, ensure_ascii=False, separators=(',', ':'))
print(f"Size of hierarquia_detalhada JSON: {len(s) / (1024*1024):.2f} MB")
