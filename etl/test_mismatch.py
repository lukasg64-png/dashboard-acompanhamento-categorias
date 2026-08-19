"""Verify column mismatch in build_single_file.py vs process_data.py"""
import os, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'data')

with open(os.path.join(DATA_DIR, 'categorias_summary.json'), 'r', encoding='utf-8') as f:
    cat = json.load(f)[0]

print("Keys in categorias_summary.json:", list(cat.keys()))

cat_keys_in_build = ['diretor','distrital','coordenador','grupo',
                     'venda_jul_26','venda_jun_26','venda_jul_25',
                     'venda_digital_jul_26','venda_digital_jun_26','venda_digital_jul_25',
                     'venda_dt_jul_26','venda_dt_jun_26','venda_dt_jul_25',
                     'mom_pct','mom_rs','yoy_pct','yoy_rs']

print("Keys in build_single_file.py:", cat_keys_in_build)
print("Match exact list?", list(cat.keys()) == cat_keys_in_build)
