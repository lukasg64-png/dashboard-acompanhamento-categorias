"""
build_setembro_dashboard.py — Compila metas (Excel) + realizado (Qlik) em JSON final
para o dashboard de acompanhamento de Setembro/2026.
Calcula desvios diários (% e nominal) por linha e empresa.
"""
import os, sys, json
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'setembro')


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calc_desvio(meta, realizado):
    """Calcula desvio nominal e percentual."""
    desvio_rs = round(realizado - meta, 2)
    desvio_pct = round((realizado / meta - 1) * 100, 2) if meta > 0 else 0.0
    return desvio_rs, desvio_pct


def build_dashboard():
    print("\n" + "=" * 60)
    print("  COMPILANDO DASHBOARD SETEMBRO — METAS vs REALIZADO")
    print("=" * 60)

    # 1. Carregar dados
    metas = load_json('metas_por_linha_dia.json')
    curva = load_json('curva_diaria.json')
    realizado = load_json('realizado_por_linha_dia.json')
    resumo = load_json('resumo_metas.json')

    if not metas or not curva:
        print("  ❌ Erro: Rode load_metas_setembro.py primeiro!")
        return

    if not realizado:
        print("  ⚠️ Sem dados de realizado. Gerando dashboard apenas com metas...")
        realizado = {'d_max': 0, 'linhas': {}, 'total_empresa_dia': [0.0]*30, 'total_empresa_acum': [0.0]*30}

    d_max = realizado.get('d_max', 0)
    print(f"  📅 D-Max Realizado: {d_max} (dias com venda)")
    print(f"  📊 Linhas com meta: {len(metas)} | Linhas com realizado: {realizado.get('total_linhas_qlik', 0)}")

    # 2. Compilar dados por linha
    linhas_dashboard = []
    real_linhas = realizado.get('linhas', {})

    for item in metas:
        nome = item['linha']
        meta_mensal = item['meta_mensal']
        meta_diaria = item['meta_diaria']
        meta_acum = item['meta_acum']
        familia = item['familia']
        categoria = item['categoria']

        # Buscar realizado (Qlik pode usar nome diferente — match case-insensitive)
        real_dia = real_linhas.get(nome, None)
        if real_dia is None:
            # Tentar match case-insensitive
            for k, v in real_linhas.items():
                if k.upper() == nome.upper():
                    real_dia = v
                    break
        if real_dia is None:
            real_dia = [0.0] * 30

        # Calcular acumulado realizado
        real_acum = []
        acum = 0.0
        for v in real_dia:
            acum += v
            real_acum.append(round(acum, 2))

        # Desvio acumulado até d_max
        meta_acum_dmax = meta_acum[d_max - 1] if d_max > 0 else 0
        real_acum_dmax = real_acum[d_max - 1] if d_max > 0 else 0
        desvio_rs, desvio_pct = calc_desvio(meta_acum_dmax, real_acum_dmax) if d_max > 0 else (0, 0)

        # Status (semáforo)
        if d_max == 0:
            status = 'aguardando'
        elif desvio_pct >= 0:
            status = 'acima'
        elif desvio_pct >= -5:
            status = 'alerta'
        else:
            status = 'abaixo'

        # Atingimento %
        ating_pct = round(real_acum_dmax / meta_acum_dmax * 100, 2) if meta_acum_dmax > 0 else 0

        grupo = item.get('grupo', 'Outros')
        subgrupo = item.get('subgrupo', 'Outros')

        linhas_dashboard.append({
            'linha': nome,
            'familia': familia,
            'categoria': categoria,
            'grupo': grupo,
            'subgrupo': subgrupo,
            'meta_mensal': meta_mensal,
            'meta_diaria': meta_diaria,
            'meta_acum': meta_acum,
            'real_dia': real_dia,
            'real_acum': real_acum,
            'meta_acum_dmax': round(meta_acum_dmax, 2),
            'real_acum_dmax': round(real_acum_dmax, 2),
            'desvio_rs': desvio_rs,
            'desvio_pct': desvio_pct,
            'ating_pct': ating_pct,
            'status': status
        })

    # Ordenar por desvio (piores primeiro para atenção)
    linhas_dashboard.sort(key=lambda x: x['desvio_rs'])

    # 3. KPIs empresa
    meta_empresa_mensal = sum(l['meta_mensal'] for l in linhas_dashboard)
    meta_empresa_acum_dmax = sum(l['meta_acum_dmax'] for l in linhas_dashboard)
    real_empresa_acum_dmax = sum(l['real_acum_dmax'] for l in linhas_dashboard)
    desvio_emp_rs, desvio_emp_pct = calc_desvio(meta_empresa_acum_dmax, real_empresa_acum_dmax) if d_max > 0 else (0, 0)
    ating_emp = round(real_empresa_acum_dmax / meta_empresa_acum_dmax * 100, 2) if meta_empresa_acum_dmax > 0 else 0

    # Evolução diária empresa (meta acum vs real acum por dia)
    evolucao_meta = [round(sum(l['meta_acum'][i] for l in linhas_dashboard), 2) for i in range(30)]
    evolucao_real = [round(sum(l['real_acum'][i] for l in linhas_dashboard), 2) for i in range(30)]

    # Contadores por status
    status_count = {'acima': 0, 'alerta': 0, 'abaixo': 0, 'aguardando': 0}
    for l in linhas_dashboard:
        status_count[l['status']] = status_count.get(l['status'], 0) + 1

    # Contadores por categoria
    cat_stats = {}
    for l in linhas_dashboard:
        cat = l['categoria'] or 'Outros'
        if cat not in cat_stats:
            cat_stats[cat] = {'meta': 0, 'real': 0, 'count': 0}
        cat_stats[cat]['meta'] += l['meta_acum_dmax']
        cat_stats[cat]['real'] += l['real_acum_dmax']
        cat_stats[cat]['count'] += 1

    for cat in cat_stats:
        s = cat_stats[cat]
        s['meta'] = round(s['meta'], 2)
        s['real'] = round(s['real'], 2)
        s['desvio_rs'] = round(s['real'] - s['meta'], 2)
        s['desvio_pct'] = round((s['real'] / s['meta'] - 1) * 100, 2) if s['meta'] > 0 else 0

    # 4. Montar JSON final
    dashboard = {
        'mes': 'Setembro/2026',
        'dias_totais': 30,
        'd_max': d_max,
        'dias_restantes': 30 - d_max,
        'ultima_atualizacao': '',

        'empresa': {
            'meta_mensal': round(meta_empresa_mensal, 2),
            'meta_acum_dmax': round(meta_empresa_acum_dmax, 2),
            'real_acum_dmax': round(real_empresa_acum_dmax, 2),
            'desvio_rs': desvio_emp_rs,
            'desvio_pct': desvio_emp_pct,
            'ating_pct': ating_emp,
            'evolucao_meta': evolucao_meta,
            'evolucao_real': evolucao_real,
        },

        'status_count': status_count,
        'categorias': cat_stats,
        'curva_diaria': curva,

        'total_linhas': len(linhas_dashboard),
        'linhas': linhas_dashboard,
    }

    # Adicionar timestamp
    from datetime import datetime
    dashboard['ultima_atualizacao'] = datetime.now().strftime('%d/%m/%Y %H:%M')

    # 5. Salvar
    out_path = os.path.join(DATA_DIR, 'dashboard_setembro.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, ensure_ascii=False)  # Sem indent para menor tamanho
    
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    
    print(f"\n  🏢 EMPRESA:")
    print(f"     Meta mês:       R$ {meta_empresa_mensal:>15,.2f}")
    print(f"     Meta acum D{d_max}:  R$ {meta_empresa_acum_dmax:>15,.2f}")
    print(f"     Realizado D{d_max}:  R$ {real_empresa_acum_dmax:>15,.2f}")
    print(f"     Desvio:         R$ {desvio_emp_rs:>15,.2f} ({desvio_emp_pct:+.2f}%)")
    print(f"     Atingimento:    {ating_emp:.1f}%")
    print(f"\n  📊 Status: 🟢 {status_count['acima']} acima | 🟡 {status_count['alerta']} alerta | 🔴 {status_count['abaixo']} abaixo | ⏳ {status_count['aguardando']} aguardando")
    print(f"  📦 Categorias: {cat_stats}")
    print(f"  💾 {out_path} ({size_mb:.1f} MB)")
    print(f"\n  🎉 Dashboard Setembro compilado com sucesso!")

    return dashboard


def main():
    build_dashboard()


if __name__ == '__main__':
    main()
