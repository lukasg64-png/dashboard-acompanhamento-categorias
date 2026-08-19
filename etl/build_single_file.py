"""
build_single_file.py — Gera HTML autocontido ultracompacto (<8.5MB) com suporte a cascata total de filtros.
"""
import os, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.basename(BASE) == 'etl':
    BASE = os.path.dirname(BASE)

DATA_DIR = os.path.join(BASE, 'data')
CSS_FILE = os.path.join(BASE, 'css', 'style.css')
JS_APP = os.path.join(BASE, 'js', 'app.js')
JS_CHARTS = os.path.join(BASE, 'js', 'charts.js')
HTML_TEMPLATE = os.path.join(BASE, 'index.html')
OUTPUT = os.path.join(BASE, 'dist', 'index.html')

def read(path):
    with open(path, 'r', encoding='utf-8') as f: return f.read()

def read_json(name):
    path = os.path.join(DATA_DIR, name if name.endswith('.json') else name + '.json')
    with open(path, 'r', encoding='utf-8') as f: return json.load(f)

def round_record(r):
    new_r = {}
    for k, v in r.items():
        if isinstance(v, list):
            if not v or all(x == 0 or x == 0.0 for x in v):
                new_r[k] = None
            else:
                new_r[k] = [int(round(x)) if isinstance(x, (int, float)) else x for x in v]
        elif isinstance(v, float):
            new_r[k] = round(v, 1)
        else:
            new_r[k] = v
    return new_r

def compress_array(records, keys):
    if not records: return {"keys": keys, "rows": []}
    rows = []
    for r in records:
        rr = round_record(r)
        rows.append([rr.get(k) for k in keys])
    return {"keys": keys, "rows": rows}

def build():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    kpis = read_json('executive_kpis.json')
    canais = read_json('canais_summary.json')
    canais_hier = read_json('canais_by_hierarquia.json')
    categorias = read_json('categorias_summary.json')
    hierarquia = read_json('hierarquia_detalhada.json')
    filtro_hier = read_json('filtro_hierarquia.json')
    filtros_prod = read_json('filtros_produto.json')

    ch_keys = ['grupo','subgrupo','linha','canal','canal_grupo','v26','v26_06','v25','d25','d26_06','d26_07']

    hier_keys = ['grupo','subgrupo','linha',
                 'venda_jul_26','venda_jun_26','venda_jul_25',
                 'venda_digital_jul_26','venda_digital_jun_26','venda_digital_jul_25',
                 'venda_dt_jul_26','venda_dt_jun_26','venda_dt_jul_25',
                 'd25','d26_06','d26_07',
                 'dig_d25','dig_d26_06','dig_d26_07',
                 'dt_d25','dt_d26_06','dt_d26_07',
                 'mom_pct','mom_rs','yoy_pct','yoy_rs']

    cat_keys = ['diretor','distrital','grupo',
                'venda_jul_26','venda_jun_26','venda_jul_25',
                'venda_digital_jul_26','venda_digital_jun_26','venda_digital_jul_25',
                'venda_dt_jul_26','venda_dt_jun_26','venda_dt_jul_25',
                'd25','d26_06','d26_07',
                'dig_d25','dig_d26_06','dig_d26_07',
                'dt_d25','dt_d26_06','dt_d26_07',
                'mom_pct','mom_rs','yoy_pct','yoy_rs']

    ch_compressed = compress_array(canais_hier, ch_keys)
    hier_compressed = compress_array(hierarquia, hier_keys)
    cat_compressed = compress_array(categorias, cat_keys)

    css = read(CSS_FILE)
    js_app = read(JS_APP)
    js_charts = read(JS_CHARTS)

    inline_block = f"""
/* ── Inline Compressed Data (auto-generated) ── */
function _decompress(packed) {{
  const keys = packed.keys;
  return packed.rows.map(row => {{
    const obj = {{}};
    for (let i = 0; i < keys.length; i++) obj[keys[i]] = row[i];
    return obj;
  }});
}}

const _PACKED = {{
  kpis: {json.dumps(kpis, ensure_ascii=False, separators=(',',':'))},
  canais: {json.dumps(canais, ensure_ascii=False, separators=(',',':'))},
  canais_hier_packed: {json.dumps(ch_compressed, ensure_ascii=False, separators=(',',':'))},
  categorias_packed: {json.dumps(cat_compressed, ensure_ascii=False, separators=(',',':'))},
  hierarquia_packed: {json.dumps(hier_compressed, ensure_ascii=False, separators=(',',':'))},
  filtroHierarquia: {json.dumps(filtro_hier, ensure_ascii=False, separators=(',',':'))},
  filtrosProduto: {json.dumps(filtros_prod, ensure_ascii=False, separators=(',',':'))}
}};
"""

    patched_app = js_app.replace(
        "async function loadAllData(mes = 'agosto') {",
        "async function loadAllData(mes = 'agosto') {\n  if (typeof _PACKED !== 'undefined') {\n    DATA.kpis = _PACKED.kpis;\n    DATA.canais = _PACKED.canais;\n    DATA.canaisHier = _decompress(_PACKED.canais_hier_packed);\n    DATA.categorias = _decompress(_PACKED.categorias_packed);\n    DATA.hierarquia = _decompress(_PACKED.hierarquia_packed);\n    DATA.filtroHierarquia = _PACKED.filtroHierarquia;\n    DATA.filtrosProduto = _PACKED.filtrosProduto;\n    return;\n  }"
    )

    html_template = read(HTML_TEMPLATE)

    html_out = html_template.replace(
        '<link rel="stylesheet" href="css/style.css">',
        f'<style>\n{css}\n</style>'
    ).replace(
        '<script src="js/app.js"></script>\n  <script src="js/charts.js"></script>',
        f'<script>\n{inline_block}\n{patched_app}\n</script>\n<script>\n{js_charts}\n</script>'
    )

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html_out)

    size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)
    print(f"[OK] HTML autocontido gerado: {OUTPUT} ({size_mb:.1f} MB)")
    return OUTPUT

if __name__ == '__main__':
    build()
