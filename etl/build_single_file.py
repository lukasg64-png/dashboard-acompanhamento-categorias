"""
build_single_file.py — Gera HTML autocontido com suporte nativo aos meses Julho (fechado) e Agosto (D-1 Qlik).
"""
import os, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.basename(BASE) == 'etl':
    BASE = os.path.dirname(BASE)

DATA_DIR = os.path.join(BASE, 'data')
AGOSTO_DIR = os.path.join(DATA_DIR, 'agosto')
CSS_FILE = os.path.join(BASE, 'css', 'style.css')
JS_APP = os.path.join(BASE, 'js', 'app.js')
JS_CHARTS = os.path.join(BASE, 'js', 'charts.js')
JS_WATERFALL = os.path.join(BASE, 'js', 'waterfall.js')
JS_METAS = os.path.join(BASE, 'js', 'metas_setembro.js')
SETEMBRO_DIR = os.path.join(DATA_DIR, 'setembro')
TEMPLATE_FILE = os.path.join(BASE, 'template.html') if os.path.exists(os.path.join(BASE, 'template.html')) else os.path.join(BASE, 'index.html')
OUTPUT_DIST = os.path.join(BASE, 'dist', 'index.html')
OUTPUT_ROOT = os.path.join(BASE, 'index.html')

def read(path):
    with open(path, 'r', encoding='utf-8') as f: return f.read()

def read_json_dir(d, name):
    path = os.path.join(d, name if name.endswith('.json') else name + '.json')
    if not os.path.exists(path):
        # Fallback to DATA_DIR
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
            new_r[k] = round(v, 2)  # Preservar precisão em centavos
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

def pack_month_dataset(folder):
    kpis = read_json_dir(folder, 'executive_kpis.json')
    canais = read_json_dir(folder, 'canais_summary.json')
    canais_hier = read_json_dir(folder, 'canais_by_hierarquia.json')
    categorias = read_json_dir(folder, 'categorias_summary.json')
    hierarquia = read_json_dir(folder, 'hierarquia_detalhada.json')
    filtro_hier = read_json_dir(folder, 'filtro_hierarquia.json')
    filtros_prod = read_json_dir(folder, 'filtros_produto.json')

    clientes_path = os.path.join(folder, 'clientes_summary.json')
    clientes = read_json_dir(folder, 'clientes_summary.json') if os.path.exists(clientes_path) else None

    ch_keys = ['diretor','distrital','grupo','subgrupo','linha','canal','canal_grupo','v26','v26_06','v25','d25','d26_06','d26_07']

    hier_keys = ['diretor','distrital','grupo','subgrupo','linha',
                 'venda_jul_26','venda_jun_26','venda_jul_25',
                 'venda_digital_jul_26','venda_digital_jun_26','venda_digital_jul_25',
                 'venda_dt_jul_26','venda_dt_jun_26','venda_dt_jul_25',
                 'd25','d26_06','d26_07',
                 'dig_d25','dig_d26_06','dig_d26_07',
                 'dt_d25','dt_d26_06','dt_d26_07',
                 'mom_pct','mom_rs','yoy_pct','yoy_rs']

    cat_keys = ['diretor','distrital','grupo','subgrupo',
                'venda_jul_26','venda_jun_26','venda_jul_25',
                'venda_digital_jul_26','venda_digital_jun_26','venda_digital_jul_25',
                'venda_dt_jul_26','venda_dt_jun_26','venda_dt_jul_25',
                'd25','d26_06','d26_07',
                'dig_d25','dig_d26_06','dig_d26_07',
                'dt_d25','dt_d26_06','dt_d26_07',
                'mom_pct','mom_rs','yoy_pct','yoy_rs']

    return {
        "kpis": kpis,
        "canais": canais,
        "canais_hier_packed": compress_array(canais_hier, ch_keys),
        "categorias_packed": compress_array(categorias, cat_keys),
        "hierarquia_packed": compress_array(hierarquia, hier_keys),
        "filtroHierarquia": filtro_hier,
        "filtrosProduto": filtros_prod,
        "clientes": clientes
    }

def build():
    os.makedirs(os.path.dirname(OUTPUT_DIST), exist_ok=True)

    print("Empacotando dataset de Julho (fechado)...")
    packed_julho = pack_month_dataset(DATA_DIR)
    
    print("Empacotando dataset de Agosto (D-1 Qlik)...")
    packed_agosto = pack_month_dataset(AGOSTO_DIR)

    css = read(CSS_FILE)
    js_app = read(JS_APP)
    js_charts = read(JS_CHARTS)
    js_waterfall = read(JS_WATERFALL) if os.path.exists(JS_WATERFALL) else ''
    js_metas = read(JS_METAS) if os.path.exists(JS_METAS) else ''

    # Load setembro dashboard data (metas vs realizado)
    setembro_dashboard_path = os.path.join(SETEMBRO_DIR, 'dashboard_setembro.json')
    setembro_data = None
    if os.path.exists(setembro_dashboard_path):
        print("Empacotando dataset de Metas Setembro...")
        with open(setembro_dashboard_path, 'r', encoding='utf-8') as f:
            setembro_data = json.load(f)

    inline_block = f"""
/* ── Inline Compressed Data (auto-generated) ── */
function _decompress(packed) {{
  if (!packed || !packed.keys || !packed.rows) return [];
  const keys = packed.keys;
  return packed.rows.map(row => {{
    const obj = {{}};
    for (let i = 0; i < keys.length; i++) obj[keys[i]] = row[i];
    return obj;
  }});
}}

const _PACKED = {{
  "julho": {json.dumps(packed_julho, ensure_ascii=False, separators=(',',':'))},
  "agosto": {json.dumps(packed_agosto, ensure_ascii=False, separators=(',',':'))}
}};

{('const _METAS_SETEMBRO = ' + json.dumps(setembro_data, ensure_ascii=False, separators=(',',':')) + ';') if setembro_data else '/* Sem dados de metas setembro */'}
"""

    patched_app = js_app.replace(
        "async function loadAllData(mes = 'agosto') {",
        "async function loadAllData(mes = 'agosto') {\n  if (typeof _PACKED !== 'undefined') {\n    const pkg = _PACKED[mes] || _PACKED['agosto'] || _PACKED['julho'];\n    if (typeof updateLoadingProgress === 'function') updateLoadingProgress(20, 'Carregando KPIs e Canais...');\n    DATA.kpis = pkg.kpis;\n    DATA.canais = pkg.canais;\n    if (typeof updateLoadingProgress === 'function') updateLoadingProgress(40, 'Descompactando Canais e Hierarquia...');\n    DATA.canaisHier = _decompress(pkg.canais_hier_packed);\n    if (typeof updateLoadingProgress === 'function') updateLoadingProgress(60, 'Descompactando Categorias...');\n    DATA.categorias = _decompress(pkg.categorias_packed);\n    if (typeof updateLoadingProgress === 'function') updateLoadingProgress(75, 'Estruturando Hierarquia...');\n    DATA.hierarquia = _decompress(pkg.hierarquia_packed);\n    DATA.filtroHierarquia = pkg.filtroHierarquia;\n    DATA.filtrosProduto = pkg.filtrosProduto;\n    DATA.clientes = pkg.clientes || null;\n    if (typeof updateLoadingProgress === 'function') updateLoadingProgress(85, 'Concluindo base de dados...');\n    return;\n  }"
    )

    html_template = read(TEMPLATE_FILE)

    html_out = html_template.replace(
        '<link rel="stylesheet" href="css/style.css">',
        f'<style>\n{css}\n</style>'
    ).replace(
        '<script src="js/app.js"></script>\n  <script src="js/charts.js"></script>\n  <script src="js/waterfall.js"></script>\n  <script src="js/metas_setembro.js"></script>',
        f'<script>\n{inline_block}\n{patched_app}\n</script>\n<script>\n{js_charts}\n</script>\n<script>\n{js_waterfall}\n</script>\n<script>\n{js_metas}\n</script>'
    )

    # Gravar tanto no dist/index.html quanto na raiz index.html (servido diretamente pelo GitHub Pages)
    os.makedirs(os.path.dirname(OUTPUT_DIST), exist_ok=True)
    with open(OUTPUT_DIST, 'w', encoding='utf-8') as f:
        f.write(html_out)

    with open(OUTPUT_ROOT, 'w', encoding='utf-8') as f:
        f.write(html_out)

    size_mb = os.path.getsize(OUTPUT_ROOT) / (1024 * 1024)
    print(f"[OK] HTML autocontido gerado com sucesso em:")
    print(f"     -> {OUTPUT_DIST} ({size_mb:.1f} MB)")
    print(f"     -> {OUTPUT_ROOT} ({size_mb:.1f} MB)")
    return OUTPUT_ROOT

if __name__ == '__main__':
    build()
