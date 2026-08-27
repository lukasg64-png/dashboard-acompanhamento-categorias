/* metas_setembro.js — Aba de Metas & Evolução Setembro/2026 (Hierarquia Grupo ➔ Subgrupo ➔ Linha) */

let METAS_DATA = null;
let _metasChart = null;
let _metasRendered = false;

// Estado de expansão da árvore
const STATE_METAS = {
  expandedGrupos: new Set(),
  expandedSubgrupos: new Set(),
  categoria: 'ALL',
  status: 'ALL',
  search: '',
  sort: 'meta_mensal' // 'meta_mensal', 'desvio_rs', 'desvio_pct', 'ating_pct', 'nome'
};

/* ── Formatação ──────────────────────────────────────── */
function _fmtRS(v) {
  if (v === null || v === undefined || isNaN(v)) return '-';
  return 'R$ ' + Math.abs(v).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function _fmtRSSigned(v) {
  if (v === null || v === undefined || isNaN(v)) return '-';
  const prefix = v > 0 ? '+' : v < 0 ? '-' : '';
  return prefix + ' R$ ' + Math.abs(v).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function _fmtPct(v) {
  if (v === null || v === undefined || isNaN(v)) return '-';
  return (v > 0 ? '+' : '') + v.toFixed(1) + '%';
}

function _escHtml(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function _statusIcon(status) {
  switch (status) {
    case 'acima': return '<span style="color:#34C759;font-size:15px;" title="Acima da meta">🟢</span>';
    case 'alerta': return '<span style="color:#FF9F0A;font-size:15px;" title="Alerta: até -5%">🟡</span>';
    case 'abaixo': return '<span style="color:#FF3B30;font-size:15px;" title="Abaixo da meta">🔴</span>';
    case 'aguardando': return '<span style="color:#8E8E93;font-size:13px;" title="Aguardando início do período D-1">⏳</span>';
    default: return '—';
  }
}

function _badgeDesvio(v, tipo) {
  if (v === null || v === undefined || isNaN(v)) return '<span class="badge neu">—</span>';
  const cls = v > 0 ? 'pos' : v < 0 ? 'neg' : 'neu';
  if (tipo === 'pct') return `<span class="badge ${cls}">${_fmtPct(v)}</span>`;
  return `<span class="delta-${cls}">${_fmtRSSigned(v)}</span>`;
}

/* ── Carregar dados ──────────────────────────────────── */
async function loadMetasData() {
  if (METAS_DATA) return METAS_DATA;

  // Se estiver embutido no single-file HTML build
  if (typeof _METAS_SETEMBRO !== 'undefined' && _METAS_SETEMBRO) {
    METAS_DATA = _METAS_SETEMBRO;
    return METAS_DATA;
  }

  // Fetch from JSON
  try {
    const ts = Date.now();
    const res = await fetch(`data/setembro/dashboard_setembro.json?v=${ts}`);
    METAS_DATA = await res.json();
    return METAS_DATA;
  } catch (e) {
    console.error('Erro ao carregar dados de metas:', e);
    return null;
  }
}

/* ── Renderizar Tab ──────────────────────────────────── */
async function renderMetasSetembroTab() {
  const data = await loadMetasData();
  if (!data) return;

  renderMetasKPIs(data);
  renderMetasChart(data);
  renderMetasHierarchicalTable(data);
  wireMetasEvents(data);
  _metasRendered = true;
}

/* ── KPIs ────────────────────────────────────────────── */
function renderMetasKPIs(data) {
  const strip = document.getElementById('kpiStripMetas');
  if (!strip) return;

  const emp = data.empresa || {};
  const dMax = data.d_max || 0;
  const diasRestantes = data.dias_restantes || 30;
  const sc = data.status_count || {};

  const atingColor = emp.ating_pct >= 100 ? '#34C759' : emp.ating_pct >= 95 ? '#FF9F0A' : emp.ating_pct > 0 ? '#FF3B30' : 'var(--text-primary)';
  const desvioColor = emp.desvio_rs > 0 ? '#34C759' : emp.desvio_rs < 0 ? '#FF3B30' : 'var(--text-secondary)';

  strip.innerHTML = `
    <div class="apple-kpi-card accent-orange">
      <div class="kpi-card-header">
        <span class="kpi-card-title">Meta Mês Total</span>
        <span class="kpi-card-badge" style="background:rgba(255,159,10,0.12);color:#cc7700;">SET/26</span>
      </div>
      <div class="kpi-value-main">${_fmtRS(emp.meta_mensal)}</div>
      <div class="kpi-sub-value">Meta Comercial +16% (598 linhas alocadas)</div>
    </div>

    <div class="apple-kpi-card accent-blue">
      <div class="kpi-card-header">
        <span class="kpi-card-title">Meta Acum. D${dMax}</span>
        <span class="kpi-card-badge" style="background:rgba(0,113,227,0.12);color:#0071E3;">D-1</span>
      </div>
      <div class="kpi-value-main">${_fmtRS(emp.meta_acum_dmax)}</div>
      <div class="kpi-sub-value">${dMax > 0 ? `Curva ponderada até dia ${dMax}` : 'Aguardando início de setembro'}</div>
    </div>

    <div class="apple-kpi-card accent-teal">
      <div class="kpi-card-header">
        <span class="kpi-card-title">Realizado Acum. D${dMax}</span>
      </div>
      <div class="kpi-value-main">${_fmtRS(emp.real_acum_dmax)}</div>
      <div class="kpi-sub-value">${dMax > 0 ? 'Venda Líquida Qlik Sense' : 'Sem vendas registradas'}</div>
    </div>

    <div class="apple-kpi-card" style="border-top: 3px solid ${desvioColor};">
      <div class="kpi-card-header">
        <span class="kpi-card-title">Desvio Acumulado</span>
      </div>
      <div class="kpi-value-main" style="color:${desvioColor};">${dMax > 0 ? _fmtRSSigned(emp.desvio_rs) : 'R$ 0'}</div>
      <div class="kpi-sub-value" style="color:${desvioColor};">${dMax > 0 ? _fmtPct(emp.desvio_pct) + ' vs meta acumulada' : 'Aguardando D-1'}</div>
    </div>

    <div class="apple-kpi-card" style="border-top: 3px solid ${atingColor};">
      <div class="kpi-card-header">
        <span class="kpi-card-title">Atingimento</span>
      </div>
      <div class="kpi-value-main" style="color:${atingColor};">${dMax > 0 && emp.ating_pct ? emp.ating_pct.toFixed(1) + '%' : '—'}</div>
      <div class="kpi-sub-value">${diasRestantes} dias restantes no mês</div>
    </div>

    <div class="apple-kpi-card accent-indigo">
      <div class="kpi-card-header">
        <span class="kpi-card-title">Status Linhas</span>
      </div>
      <div class="kpi-value-main" style="font-size: 17px;">
        🟢 ${sc.acima || 0} &nbsp; 🟡 ${sc.alerta || 0} &nbsp; 🔴 ${sc.abaixo || 0}
      </div>
      <div class="kpi-sub-value">⏳ ${sc.aguardando || 0} aguardando início de Set/26</div>
    </div>
  `;
}

/* ── Gráfico Evolução ────────────────────────────────── */
function renderMetasChart(data) {
  const canvas = document.getElementById('chartMetasEvolucao');
  if (!canvas || typeof Chart === 'undefined') return;

  const emp = data.empresa || {};
  const dMax = data.d_max || 0;
  const curva = data.curva_diaria || [];

  const labels = curva.map(d => `D${d.dia}`);
  const metaAcum = emp.evolucao_meta || curva.map(d => d.meta_acum);
  const realAcum = emp.evolucao_real || [];

  if (_metasChart) _metasChart.destroy();

  _metasChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Meta Acumulada R$',
          data: metaAcum,
          borderColor: '#FF9F0A',
          backgroundColor: 'rgba(255, 159, 10, 0.08)',
          borderWidth: 2.5,
          borderDash: [6, 4],
          fill: false,
          tension: 0.3,
          pointRadius: 0,
          pointHoverRadius: 5,
        },
        {
          label: 'Realizado Acumulado R$',
          data: realAcum.map((v, i) => i < dMax ? v : null),
          borderColor: '#0071E3',
          backgroundColor: 'rgba(0, 113, 227, 0.12)',
          borderWidth: 3,
          fill: true,
          tension: 0.3,
          pointRadius: (ctx) => ctx.dataIndex === dMax - 1 ? 6 : 0,
          pointBackgroundColor: '#0071E3',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointHoverRadius: 7,
        },
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          labels: { usePointStyle: true, padding: 20, font: { size: 12, weight: 600 } }
        },
        tooltip: {
          backgroundColor: 'rgba(0,0,0,0.85)',
          titleFont: { size: 13, weight: 700 },
          bodyFont: { size: 12 },
          padding: 12,
          cornerRadius: 10,
          callbacks: {
            label: function(ctx) {
              const v = ctx.parsed.y;
              if (v === null || v === undefined) return '';
              return `${ctx.dataset.label}: R$ ${(v/1e6).toFixed(1)}M`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 10 }, maxRotation: 0 }
        },
        y: {
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: {
            font: { size: 10 },
            callback: v => 'R$ ' + (v / 1e6).toFixed(0) + 'M'
          }
        }
      }
    }
  });

  const sub = document.getElementById('metasEvolucaoSubtitle');
  if (sub) {
    sub.textContent = dMax > 0
      ? `Setembro/2026 • D-1 até dia ${dMax} • Atualizado: ${data.ultima_atualizacao || ''}`
      : 'Setembro/2026 • Curva diária ponderada (30 dias) • Aguardando início do mês';
  }
}

/* ── Toggle Expand / Collapse ─────────────────────────── */
function toggleMetasGrupo(grupoNome) {
  if (STATE_METAS.expandedGrupos.has(grupoNome)) {
    STATE_METAS.expandedGrupos.delete(grupoNome);
  } else {
    STATE_METAS.expandedGrupos.add(grupoNome);
  }
  renderMetasHierarchicalTable(METAS_DATA);
}

function toggleMetasSubgrupo(subKey) {
  if (STATE_METAS.expandedSubgrupos.has(subKey)) {
    STATE_METAS.expandedSubgrupos.delete(subKey);
  } else {
    STATE_METAS.expandedSubgrupos.add(subKey);
  }
  renderMetasHierarchicalTable(METAS_DATA);
}

/* ── Tabela Hierárquica: Grupo ➔ Subgrupo ➔ Linha ────── */
function renderMetasHierarchicalTable(data) {
  const tbody = document.getElementById('tbodyMetasLinhas');
  const countEl = document.getElementById('metasTableCount');
  if (!tbody || !data) return;

  const dMax = data.d_max || 0;
  const catFilter = STATE_METAS.categoria;
  const statusFilter = STATE_METAS.status;
  const searchTerm = STATE_METAS.search.toLowerCase().trim();
  const sortMode = STATE_METAS.sort;

  // 1. Filtrar linhas de produto
  let filteredLinhas = (data.linhas || []).filter(l => {
    if (catFilter !== 'ALL' && l.categoria !== catFilter) return false;
    if (statusFilter !== 'ALL' && l.status !== statusFilter) return false;
    if (searchTerm) {
      const match = l.linha.toLowerCase().includes(searchTerm) ||
                    (l.subgrupo || '').toLowerCase().includes(searchTerm) ||
                    (l.grupo || '').toLowerCase().includes(searchTerm) ||
                    (l.familia || '').toLowerCase().includes(searchTerm);
      if (!match) return false;
    }
    return true;
  });

  // Se houver busca ativa, expande automaticamente grupos e subgrupos correspondentes
  if (searchTerm) {
    filteredLinhas.forEach(l => {
      STATE_METAS.expandedGrupos.add(l.grupo);
      STATE_METAS.expandedSubgrupos.add(`${l.grupo}||${l.subgrupo}`);
    });
  }

  // 2. Construir árvore hierárquica (Grupo ➔ Subgrupo ➔ Linhas)
  const tree = {};
  filteredLinhas.forEach(l => {
    const g = l.grupo || 'Outros';
    const sg = l.subgrupo || 'Geral';

    if (!tree[g]) {
      tree[g] = {
        nome: g,
        subgrupos: {},
        meta_mensal: 0,
        meta_acum_dmax: 0,
        real_acum_dmax: 0,
        linhasCount: 0,
        categorias: new Set()
      };
    }

    if (!tree[g].subgrupos[sg]) {
      tree[g].subgrupos[sg] = {
        nome: sg,
        grupoNome: g,
        key: `${g}||${sg}`,
        linhas: [],
        meta_mensal: 0,
        meta_acum_dmax: 0,
        real_acum_dmax: 0,
        categorias: new Set()
      };
    }

    tree[g].subgrupos[sg].linhas.push(l);
    tree[g].subgrupos[sg].meta_mensal += l.meta_mensal;
    tree[g].subgrupos[sg].meta_acum_dmax += l.meta_acum_dmax;
    tree[g].subgrupos[sg].real_acum_dmax += l.real_acum_dmax;
    tree[g].subgrupos[sg].categorias.add(l.categoria);

    tree[g].meta_mensal += l.meta_mensal;
    tree[g].meta_acum_dmax += l.meta_acum_dmax;
    tree[g].real_acum_dmax += l.real_acum_dmax;
    tree[g].linhasCount += 1;
    tree[g].categorias.add(l.categoria);
  });

  // 3. Converter para array de grupos e ordenar
  const gruposList = Object.values(tree);
  gruposList.forEach(g => {
    g.desvio_rs = g.real_acum_dmax - g.meta_acum_dmax;
    g.desvio_pct = g.meta_acum_dmax > 0 ? (g.real_acum_dmax / g.meta_acum_dmax - 1) * 100 : 0;
    g.ating_pct = g.meta_acum_dmax > 0 ? (g.real_acum_dmax / g.meta_acum_dmax * 100) : 0;
    g.status = dMax === 0 ? 'aguardando' : g.desvio_pct >= 0 ? 'acima' : g.desvio_pct >= -5 ? 'alerta' : 'abaixo';

    // Ordenar subgrupos dentro do grupo
    g.subgruposList = Object.values(g.subgrupos);
    g.subgruposList.forEach(sg => {
      sg.desvio_rs = sg.real_acum_dmax - sg.meta_acum_dmax;
      sg.desvio_pct = sg.meta_acum_dmax > 0 ? (sg.real_acum_dmax / sg.meta_acum_dmax - 1) * 100 : 0;
      sg.ating_pct = sg.meta_acum_dmax > 0 ? (sg.real_acum_dmax / sg.meta_acum_dmax * 100) : 0;
      sg.status = dMax === 0 ? 'aguardando' : sg.desvio_pct >= 0 ? 'acima' : sg.desvio_pct >= -5 ? 'alerta' : 'abaixo';

      // Ordenar linhas dentro do subgrupo
      switch (sortMode) {
        case 'meta_mensal': sg.linhas.sort((a, b) => b.meta_mensal - a.meta_mensal); break;
        case 'desvio_rs': sg.linhas.sort((a, b) => a.desvio_rs - b.desvio_rs); break;
        case 'desvio_pct': sg.linhas.sort((a, b) => a.desvio_pct - b.desvio_pct); break;
        case 'ating_pct': sg.linhas.sort((a, b) => a.ating_pct - b.ating_pct); break;
        case 'nome': sg.linhas.sort((a, b) => a.linha.localeCompare(b.linha)); break;
      }
    });

    // Ordenar subgrupos por maior meta
    g.subgruposList.sort((a, b) => b.meta_mensal - a.meta_mensal);
  });

  // Ordenar grupos pelo critério selecionado
  switch (sortMode) {
    case 'meta_mensal': gruposList.sort((a, b) => b.meta_mensal - a.meta_mensal); break;
    case 'desvio_rs': gruposList.sort((a, b) => a.desvio_rs - b.desvio_rs); break;
    case 'desvio_pct': gruposList.sort((a, b) => a.desvio_pct - b.desvio_pct); break;
    case 'ating_pct': gruposList.sort((a, b) => a.ating_pct - b.ating_pct); break;
    case 'nome': gruposList.sort((a, b) => a.nome.localeCompare(b.nome)); break;
  }

  // 4. Renderizar HTML
  let html = '';
  let totalMetaGeral = 0;
  let totalMetaAcumGeral = 0;
  let totalRealGeral = 0;

  gruposList.forEach(g => {
    totalMetaGeral += g.meta_mensal;
    totalMetaAcumGeral += g.meta_acum_dmax;
    totalRealGeral += g.real_acum_dmax;

    const isExpGrupo = STATE_METAS.expandedGrupos.has(g.nome);
    const toggleIconGrupo = isExpGrupo ? '▼' : '▶';

    let catBadgeGrupo = '';
    if (g.categorias.size === 1) {
      catBadgeGrupo = g.categorias.has('Medicamento')
        ? '<span style="color:#5856D6;font-weight:600;">💊 Med</span>'
        : '<span style="color:#FF9F0A;font-weight:600;">🛍️ NMed</span>';
    } else {
      catBadgeGrupo = '<span style="color:var(--text-tertiary);">Misto</span>';
    }

    // Linha Nível 1: GRUPO
    html += `
      <tr class="row-group" style="background: rgba(0, 113, 227, 0.05); cursor: pointer; font-weight: 700;" onclick="toggleMetasGrupo('${_escHtml(g.nome)}')">
        <td style="position: sticky; left: 0; z-index: 6; background: #F2F7FD; padding: 10px 14px;">
          <span class="toggle-icon" style="display:inline-flex;width:18px;height:18px;align-items:center;justify-content:center;background:rgba(0,113,227,0.12);color:var(--apple-blue);border-radius:4px;font-size:10px;margin-right:8px;">${toggleIconGrupo}</span>
          <strong style="color: var(--apple-blue); font-size: 13px;">${_escHtml(g.nome)}</strong>
          <span style="font-size: 10.5px; color: var(--text-tertiary); font-weight: 500; margin-left: 6px;">(${g.subgruposList.length} subgrupos • ${g.linhasCount} linhas)</span>
        </td>
        <td class="num" style="font-size: 11px; font-weight: 700; color: var(--apple-blue);">GRUPO</td>
        <td class="num" style="font-size: 11px;">${catBadgeGrupo}</td>
        <td class="num font-weight-600" style="font-size: 12.5px;">${_fmtRS(g.meta_mensal)}</td>
        <td class="num">${_fmtRS(g.meta_acum_dmax)}</td>
        <td class="num font-weight-600">${dMax > 0 ? _fmtRS(g.real_acum_dmax) : '—'}</td>
        <td class="num">${dMax > 0 ? _badgeDesvio(g.desvio_rs, 'rs') : '—'}</td>
        <td class="num">${dMax > 0 ? _badgeDesvio(g.desvio_pct, 'pct') : '—'}</td>
        <td class="num">${dMax > 0 ? `<strong>${g.ating_pct.toFixed(1)}%</strong>` : '—'}</td>
        <td class="num">${_statusIcon(g.status)}</td>
      </tr>
    `;

    // Se Grupo estiver expandido, renderiza os SUBGRUPOS
    if (isExpGrupo) {
      g.subgruposList.forEach(sg => {
        const isExpSub = STATE_METAS.expandedSubgrupos.has(sg.key);
        const toggleIconSub = isExpSub ? '▼' : '▶';

        let catBadgeSub = '';
        if (sg.categorias.size === 1) {
          catBadgeSub = sg.categorias.has('Medicamento')
            ? '<span style="color:#5856D6;font-size:10px;">💊 Med</span>'
            : '<span style="color:#FF9F0A;font-size:10px;">🛍️ NMed</span>';
        } else {
          catBadgeSub = '<span style="color:var(--text-tertiary);font-size:10px;">Misto</span>';
        }

        // Linha Nível 2: SUBGRUPO
        html += `
          <tr class="row-subgrupo" style="background: rgba(0,0,0,0.015); cursor: pointer;" onclick="toggleMetasSubgrupo('${_escHtml(sg.key)}')">
            <td style="position: sticky; left: 0; z-index: 5; background: #FAFAFC; padding-left: 28px;">
              <span class="toggle-icon" style="display:inline-flex;width:16px;height:16px;align-items:center;justify-content:center;background:rgba(0,0,0,0.06);color:var(--text-secondary);border-radius:3px;font-size:9px;margin-right:6px;">${toggleIconSub}</span>
              <strong style="color: var(--text-primary); font-size: 12px;">${_escHtml(sg.nome)}</strong>
              <span style="font-size: 10px; color: var(--text-tertiary); margin-left: 4px;">(${sg.linhas.length} linhas)</span>
            </td>
            <td class="num" style="font-size: 10.5px; color: var(--text-secondary);">Subgrupo</td>
            <td class="num">${catBadgeSub}</td>
            <td class="num font-weight-600">${_fmtRS(sg.meta_mensal)}</td>
            <td class="num">${_fmtRS(sg.meta_acum_dmax)}</td>
            <td class="num font-weight-600">${dMax > 0 ? _fmtRS(sg.real_acum_dmax) : '—'}</td>
            <td class="num">${dMax > 0 ? _badgeDesvio(sg.desvio_rs, 'rs') : '—'}</td>
            <td class="num">${dMax > 0 ? _badgeDesvio(sg.desvio_pct, 'pct') : '—'}</td>
            <td class="num">${dMax > 0 ? `<strong>${sg.ating_pct.toFixed(1)}%</strong>` : '—'}</td>
            <td class="num">${_statusIcon(sg.status)}</td>
          </tr>
        `;

        // Se Subgrupo estiver expandido, renderiza as LINHAS
        if (isExpSub) {
          sg.linhas.forEach(l => {
            const catBadgeLinha = l.categoria === 'Medicamento'
              ? '<span style="color:#5856D6;font-size:10px;">💊 Med</span>'
              : '<span style="color:#FF9F0A;font-size:10px;">🛍️ NMed</span>';

            // Linha Nível 3: LINHA DE PRODUTO
            html += `
              <tr class="row-linha" style="background: #FFFFFF;">
                <td style="position: sticky; left: 0; z-index: 4; background: #FFFFFF; padding-left: 50px;">
                  <span style="color: var(--text-tertiary); margin-right: 6px;">↳</span>
                  <span style="font-weight: 500; color: var(--text-primary); font-size: 11.5px;">${_escHtml(l.linha)}</span>
                </td>
                <td class="num" style="font-size: 10px; color: var(--text-tertiary);">${_escHtml(l.familia || '—')}</td>
                <td class="num">${catBadgeLinha}</td>
                <td class="num font-weight-600">${_fmtRS(l.meta_mensal)}</td>
                <td class="num">${_fmtRS(l.meta_acum_dmax)}</td>
                <td class="num font-weight-600">${dMax > 0 ? _fmtRS(l.real_acum_dmax) : '—'}</td>
                <td class="num">${dMax > 0 ? _badgeDesvio(l.desvio_rs, 'rs') : '—'}</td>
                <td class="num">${dMax > 0 ? _badgeDesvio(l.desvio_pct, 'pct') : '—'}</td>
                <td class="num">${dMax > 0 ? `<strong>${l.ating_pct.toFixed(1)}%</strong>` : '—'}</td>
                <td class="num">${_statusIcon(l.status)}</td>
              </tr>
            `;
          });
        }
      });
    }
  });

  // 5. Linha de TOTAL GERAL (soma 100% precisa dos Grupos)
  const totalDesvioGeral = totalRealGeral - totalMetaAcumGeral;
  const totalDesvioPctGeral = totalMetaAcumGeral > 0 ? (totalRealGeral / totalMetaAcumGeral - 1) * 100 : 0;
  const totalAtingGeral = totalMetaAcumGeral > 0 ? (totalRealGeral / totalMetaAcumGeral * 100) : 0;

  html += `
    <tr style="font-weight: 800; background: rgba(0, 113, 227, 0.08); border-top: 2.5px solid var(--border); border-bottom: 2.5px solid var(--border); font-size: 12.5px;">
      <td style="position: sticky; left: 0; z-index: 7; background: #EDF4FD; padding: 12px 14px;">
        <strong style="color: var(--apple-blue);">TOTAL GERAL (${gruposList.length} Grupos • ${filteredLinhas.length} Linhas)</strong>
      </td>
      <td class="num" style="color: var(--apple-blue);">TOTAL</td>
      <td class="num">${catFilter !== 'ALL' ? (catFilter === 'Medicamento' ? '💊 Med' : '🛍️ NMed') : 'Todos'}</td>
      <td class="num" style="font-weight: 800; color: var(--text-primary);">${_fmtRS(totalMetaGeral)}</td>
      <td class="num" style="font-weight: 700;">${_fmtRS(totalMetaAcumGeral)}</td>
      <td class="num" style="font-weight: 800;">${dMax > 0 ? _fmtRS(totalRealGeral) : '—'}</td>
      <td class="num">${dMax > 0 ? _badgeDesvio(totalDesvioGeral, 'rs') : '—'}</td>
      <td class="num">${dMax > 0 ? _badgeDesvio(totalDesvioPctGeral, 'pct') : '—'}</td>
      <td class="num">${dMax > 0 ? `<strong>${totalAtingGeral.toFixed(1)}%</strong>` : '—'}</td>
      <td class="num"></td>
    </tr>
  `;

  tbody.innerHTML = html;

  if (countEl) {
    const totalLinesAll = (data.linhas || []).length;
    countEl.textContent = `${filteredLinhas.length} linhas em ${gruposList.length} grupos${filteredLinhas.length < totalLinesAll ? ` (filtrado de ${totalLinesAll})` : ''}`;
  }
}

/* ── Wire Events (Filtros, Busca e Botões da Árvore) ─── */
let _metasEventsWired = false;
function wireMetasEvents(data) {
  if (_metasEventsWired) return;
  _metasEventsWired = true;

  const catSel = document.getElementById('metasFilterCategoria');
  const statusSel = document.getElementById('metasFilterStatus');
  const searchInput = document.getElementById('metasSearch');
  const sortSel = document.getElementById('metasSortMode');

  const btnExpandGrupos = document.getElementById('btnMetasExpandGrupos');
  const btnExpandAll = document.getElementById('btnMetasExpandAll');
  const btnCollapseAll = document.getElementById('btnMetasCollapseAll');

  function updateTable() {
    if (catSel) STATE_METAS.categoria = catSel.value;
    if (statusSel) STATE_METAS.status = statusSel.value;
    if (searchInput) STATE_METAS.search = searchInput.value;
    if (sortSel) STATE_METAS.sort = sortSel.value;
    renderMetasHierarchicalTable(data);
  }

  if (catSel) catSel.addEventListener('change', updateTable);
  if (statusSel) statusSel.addEventListener('change', updateTable);
  if (searchInput) searchInput.addEventListener('input', updateTable);
  if (sortSel) sortSel.addEventListener('change', updateTable);

  // Botões de Expansão / Recolhimento da Árvore
  if (btnExpandGrupos) {
    btnExpandGrupos.addEventListener('click', () => {
      // Expande apenas os grupos (mostra subgrupos)
      (data.linhas || []).forEach(l => {
        if (l.grupo) STATE_METAS.expandedGrupos.add(l.grupo);
      });
      renderMetasHierarchicalTable(data);
    });
  }

  if (btnExpandAll) {
    btnExpandAll.addEventListener('click', () => {
      // Expande tudo (grupos e subgrupos)
      (data.linhas || []).forEach(l => {
        if (l.grupo) STATE_METAS.expandedGrupos.add(l.grupo);
        if (l.grupo && l.subgrupo) STATE_METAS.expandedSubgrupos.add(`${l.grupo}||${l.subgrupo}`);
      });
      renderMetasHierarchicalTable(data);
    });
  }

  if (btnCollapseAll) {
    btnCollapseAll.addEventListener('click', () => {
      // Recolhe tudo
      STATE_METAS.expandedGrupos.clear();
      STATE_METAS.expandedSubgrupos.clear();
      renderMetasHierarchicalTable(data);
    });
  }
}

/* ── Pre-load on DOM ready ───────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  loadMetasData();
});
