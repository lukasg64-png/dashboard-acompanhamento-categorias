/* metas_setembro.js — Metas & Evolução Setembro/2026:
   1) Aba 4: Macro Empresa & Categorias (tabMetasSetembro)
   2) Aba 5: Metas por Diretoria & Distritais (tabMetasDiretoria)
*/

let METAS_DATA = null;
let _metasChart = null;
let _metasRendered = false;
let _dirRendered = false;

// Estado de filtros da Aba Macro Empresa
const STATE_METAS = {
  categoria: 'ALL',
  status: 'ALL',
  search: '',
  sort: 'meta_mensal'
};

// Estado de filtros e expansão da Aba Diretoria & Distritais
const STATE_DIR = {
  diretoria: 'ALL',
  distrital: 'ALL',
  grupo: 'ALL',
  search: '',
  expandedDirs: new Set(['Cintia Silva', 'Laerti Siqueira']),
  expandedDists: new Set(),
  expandedGrupos: new Set()
};

/* ── Formatação ──────────────────────────────────────── */
function _fmtRS(v) {
  if (v === null || v === undefined || isNaN(v)) return '-';
  return 'R$ ' + Math.abs(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function _fmtRSCompact(v) {
  if (v === null || v === undefined || isNaN(v)) return '-';
  const val = Math.abs(v);
  if (val >= 1e9) return 'R$ ' + (val / 1e9).toFixed(2).replace('.', ',') + ' B';
  if (val >= 1e6) return 'R$ ' + (val / 1e6).toFixed(2).replace('.', ',') + ' M';
  if (val >= 1e3) return 'R$ ' + (val / 1e3).toFixed(1).replace('.', ',') + ' mil';
  return 'R$ ' + val.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function _fmtRSSigned(v) {
  if (v === null || v === undefined || isNaN(v)) return '-';
  const prefix = v > 0 ? '+' : v < 0 ? '-' : '';
  return prefix + ' R$ ' + Math.abs(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function _fmtPct(v) {
  if (v === null || v === undefined || isNaN(v)) return '-';
  return (v > 0 ? '+' : '') + v.toFixed(1).replace('.', ',') + '%';
}

function _escHtml(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function _statusIcon(status) {
  switch (status) {
    case 'acima': return '<span style="color:#34C759;font-size:14px;" title="Acima da meta">🟢</span>';
    case 'alerta': return '<span style="color:#FF9F0A;font-size:14px;" title="Alerta: até -5%">🟡</span>';
    case 'abaixo': return '<span style="color:#FF3B30;font-size:14px;" title="Abaixo da meta">🔴</span>';
    case 'aguardando': return '<span style="color:#8E8E93;font-size:13px;" title="Aguardando dados">⏳</span>';
    default: return '—';
  }
}

function _badgeAting(ating_pct) {
  if (ating_pct === null || ating_pct === undefined || isNaN(ating_pct)) return '<span class="apple-tag tag-neu">—</span>';
  if (ating_pct >= 100) return `<span class="apple-tag tag-pos">${ating_pct.toFixed(1).replace('.', ',')}%</span>`;
  if (ating_pct >= 95) return `<span class="apple-tag tag-neu" style="color:var(--apple-orange);background:var(--apple-orange-soft);">${ating_pct.toFixed(1).replace('.', ',')}%</span>`;
  return `<span class="apple-tag tag-neg">${ating_pct.toFixed(1).replace('.', ',')}%</span>`;
}

function _badgeDesvio(v, tipo) {
  if (v === null || v === undefined || isNaN(v)) return '<span class="apple-tag tag-neu">—</span>';
  const cls = v > 0 ? 'tag-pos' : v < 0 ? 'tag-neg' : 'tag-neu';
  if (tipo === 'pct') return `<span class="apple-tag ${cls}">${_fmtPct(v)}</span>`;
  return `<span class="apple-tag ${cls}">${_fmtRSSigned(v)}</span>`;
}

/* ── Carregar dados ──────────────────────────────────── */
async function loadMetasData() {
  if (METAS_DATA) return METAS_DATA;

  if (typeof _METAS_SETEMBRO !== 'undefined' && _METAS_SETEMBRO) {
    METAS_DATA = _METAS_SETEMBRO;
    return METAS_DATA;
  }

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

/* ==========================================================================
   ABA 4: MACRO EMPRESA & CATEGORIAS (tabMetasSetembro)
   ========================================================================== */
async function renderMetasSetembroTab() {
  const data = await loadMetasData();
  if (!data) return;

  renderMetasKPIs(data);
  renderMetasChart(data);
  renderMetasGruposEmpresa(data);
  renderMetasLinhasTable(data);
  wireMetasMacroEvents(data);
  _metasRendered = true;
}

function renderMetasKPIs(data) {
  const strip = document.getElementById('kpiStripMetas');
  if (!strip) return;

  const emp = data.empresa || {};
  const dMax = data.d_max || 1;
  const diasRestantes = data.dias_restantes || 29;

  strip.innerHTML = `
    <!-- Card 1: Meta Mensal -->
    <div class="apple-kpi-card accent-blue">
      <div class="kpi-card-header">
        <span class="kpi-card-title">META SETEMBRO/2026</span>
        <span class="apple-tag tag-neu">Mês Completo</span>
      </div>
      <div class="kpi-value-main" style="color:var(--apple-blue);">${_fmtRSCompact(emp.meta_mensal)}</div>
      <div class="kpi-sub-value">${_fmtRS(emp.meta_mensal)} total empresa</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">Alocação Distrital × Linhas</span>
      </div>
    </div>

    <!-- Card 2: Meta Esperada D-1 -->
    <div class="apple-kpi-card accent-indigo">
      <div class="kpi-card-header">
        <span class="kpi-card-title">META ACUM. ATÉ D-1</span>
        <span class="apple-tag tag-neu">Dia ${dMax} de 30</span>
      </div>
      <div class="kpi-value-main" style="color:var(--apple-indigo);">${_fmtRSCompact(emp.meta_acum_dmax)}</div>
      <div class="kpi-sub-value">${_fmtRS(emp.meta_acum_dmax)} acumulado esperado</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">${(dMax / 30 * 100).toFixed(1)}% do mês decorrido</span>
      </div>
    </div>

    <!-- Card 3: Realizado D-1 -->
    <div class="apple-kpi-card accent-green">
      <div class="kpi-card-header">
        <span class="kpi-card-title">REALIZADO D-1 QLIK</span>
        <span class="apple-tag tag-pos">Resultado Líquido</span>
      </div>
      <div class="kpi-value-main" style="color:var(--apple-green-text);">${_fmtRSCompact(emp.real_acum_dmax)}</div>
      <div class="kpi-sub-value">${_fmtRS(emp.real_acum_dmax)} faturado</div>
      <div class="kpi-footer-deltas">
        ${_badgeAting(emp.ating_pct)} <span class="sublabel">Atingimento D-1</span>
      </div>
    </div>

    <!-- Card 4: Desvio vs Meta -->
    <div class="apple-kpi-card ${emp.desvio_rs >= 0 ? 'accent-green' : 'accent-red'}">
      <div class="kpi-card-header">
        <span class="kpi-card-title">DESVIO D-1 vs META</span>
        ${_badgeDesvio(emp.desvio_pct, 'pct')}
      </div>
      <div class="kpi-value-main" style="color:${emp.desvio_rs >= 0 ? 'var(--apple-green-text)' : 'var(--apple-red-text)'};">${_fmtRSSigned(emp.desvio_rs)}</div>
      <div class="kpi-sub-value">${emp.desvio_rs >= 0 ? 'Superando a meta diária' : 'Abaixo da meta esperada'}</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">Diferença nominal acumulada</span>
      </div>
    </div>

    <!-- Card 5: Projeção Run-Rate -->
    <div class="apple-kpi-card accent-orange">
      <div class="kpi-card-header">
        <span class="kpi-card-title">PROJEÇÃO RUN-RATE</span>
        <span class="apple-tag tag-neu">Ritmo Atual</span>
      </div>
      <div class="kpi-value-main" style="color:var(--apple-orange);">${_fmtRSCompact(emp.projecao_runrate)}</div>
      <div class="kpi-sub-value">${_fmtRS(emp.projecao_runrate)} fechamento estimado</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">Baseado na média diária de vendas</span>
      </div>
    </div>

    <!-- Card 6: Dias Restantes -->
    <div class="apple-kpi-card accent-teal">
      <div class="kpi-card-header">
        <span class="kpi-card-title">DIAS RESTANTES</span>
        <span class="apple-tag tag-neu">Setembro</span>
      </div>
      <div class="kpi-value-main" style="color:var(--apple-teal);">${diasRestantes} dias</div>
      <div class="kpi-sub-value">Necessário: ${_fmtRSCompact((emp.meta_mensal - emp.real_acum_dmax) / Math.max(1, diasRestantes))}/dia</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">Para atingir 100% da meta</span>
      </div>
    </div>
  `;
}

function renderMetasChart(data) {
  const canvas = document.getElementById('chartMetasEvolucao');
  if (!canvas) return;

  const emp = data.empresa || {};
  const curva = data.curva_diaria || [];
  const dMax = data.d_max || 1;

  const labels = curva.map(c => `Dia ${c.dia}`);
  const metaAcum = emp.evolucao_meta || curva.map(c => c.meta_acum);
  const realAcum = (emp.evolucao_real || []).map((v, i) => i < dMax ? v : null);

  if (_metasChart) _metasChart.destroy();

  _metasChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Meta Acumulada R$',
          data: metaAcum,
          borderColor: '#0071E3',
          backgroundColor: 'rgba(0, 113, 227, 0.08)',
          fill: true,
          tension: 0.3,
          borderWidth: 2.5,
          pointRadius: 2
        },
        {
          label: 'Realizado Acumulado R$',
          data: realAcum,
          borderColor: '#34C759',
          backgroundColor: 'rgba(52, 199, 89, 0.15)',
          fill: true,
          tension: 0.3,
          borderWidth: 3,
          pointRadius: 5,
          pointBackgroundColor: '#34C759'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12, font: { weight: 600 } } },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: R$ ${(ctx.raw || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
          }
        }
      },
      scales: {
        y: {
          ticks: { callback: (v) => 'R$ ' + (v / 1e6).toFixed(0) + 'M' },
          grid: { color: 'rgba(0,0,0,0.04)' }
        },
        x: { grid: { display: false } }
      }
    }
  });
}

function renderMetasGruposEmpresa(data) {
  const tbody = document.getElementById('tbodyMetasGruposEmpresa');
  if (!tbody) return;

  const grupos = data.grupos || [];
  let html = '';

  grupos.forEach(g => {
    html += `
      <tr class="row-linha">
        <td style="font-weight: 700; color: var(--text-primary);">${_escHtml(g.grupo)}</td>
        <td class="num font-weight-600">${_fmtRS(g.meta_mensal)}</td>
        <td class="num">${g.share_meta.toFixed(1).replace('.', ',')}%</td>
        <td class="num">${_fmtRS(g.meta_acum_dmax)}</td>
        <td class="num font-weight-600" style="color:var(--apple-blue);">${_fmtRS(g.real_acum_dmax)}</td>
        <td class="num">${_fmtRSSigned(g.desvio_rs)}</td>
        <td class="num">${_badgeDesvio(g.desvio_pct, 'pct')}</td>
        <td class="num">${_badgeAting(g.ating_pct)}</td>
        <td class="num">${g.total_linhas}</td>
        <td class="num">${_statusIcon(g.status)}</td>
      </tr>
    `;
  });

  tbody.innerHTML = html;

  // Preencher Select de Categorias/Grupos
  const selCat = document.getElementById('metasFilterCategoria');
  if (selCat && selCat.options.length <= 1) {
    grupos.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.grupo;
      opt.textContent = g.grupo;
      selCat.appendChild(opt);
    });
  }
}

function renderMetasLinhasTable(data) {
  const tbody = document.getElementById('tbodyMetasLinhas');
  if (!tbody) return;

  let linhas = [...(data.linhas || [])];

  // Filtros
  if (STATE_METAS.categoria !== 'ALL') {
    linhas = linhas.filter(l => l.grupo === STATE_METAS.categoria || l.categoria === STATE_METAS.categoria);
  }
  if (STATE_METAS.status !== 'ALL') {
    linhas = linhas.filter(l => l.status === STATE_METAS.status);
  }
  if (STATE_METAS.search.trim()) {
    const q = STATE_METAS.search.trim().toLowerCase();
    linhas = linhas.filter(l => l.linha.toLowerCase().includes(q) || (l.familia && l.familia.toLowerCase().includes(q)) || (l.grupo && l.grupo.toLowerCase().includes(q)));
  }

  // Ordenação
  switch (STATE_METAS.sort) {
    case 'meta_mensal':
      linhas.sort((a, b) => b.meta_mensal - a.meta_mensal);
      break;
    case 'desvio_rs':
      linhas.sort((a, b) => a.desvio_rs - b.desvio_rs);
      break;
    case 'desvio_pct':
      linhas.sort((a, b) => a.desvio_pct - b.desvio_pct);
      break;
    case 'ating_pct':
      linhas.sort((a, b) => b.ating_pct - a.ating_pct);
      break;
    case 'linha':
      linhas.sort((a, b) => a.linha.localeCompare(b.linha));
      break;
  }

  const countEl = document.getElementById('metasTableCount');
  if (countEl) countEl.textContent = `${linhas.length} linhas`;

  let html = '';
  linhas.forEach(l => {
    html += `
      <tr class="row-linha">
        <td style="font-weight: 600; color: var(--text-primary);">${_escHtml(l.linha)}</td>
        <td class="num">${_escHtml(l.grupo || '-')}</td>
        <td class="num">${_escHtml(l.subgrupo || l.familia || '-')}</td>
        <td class="num font-weight-600">${_fmtRS(l.meta_mensal)}</td>
        <td class="num">${_fmtRS(l.meta_acum_dmax)}</td>
        <td class="num font-weight-600" style="color:var(--apple-blue);">${_fmtRS(l.real_acum_dmax)}</td>
        <td class="num">${_fmtRSSigned(l.desvio_rs)}</td>
        <td class="num">${_badgeDesvio(l.desvio_pct, 'pct')}</td>
        <td class="num">${_badgeAting(l.ating_pct)}</td>
        <td class="num">${_statusIcon(l.status)}</td>
      </tr>
    `;
  });

  tbody.innerHTML = html || '<tr><td colspan="10" style="text-align:center;padding:24px;color:var(--text-tertiary);">Nenhuma linha encontrada com os filtros selecionados.</td></tr>';
}

function wireMetasMacroEvents(data) {
  const selCat = document.getElementById('metasFilterCategoria');
  if (selCat) {
    selCat.onchange = (e) => {
      STATE_METAS.categoria = e.target.value;
      renderMetasLinhasTable(data);
    };
  }

  const selStatus = document.getElementById('metasFilterStatus');
  if (selStatus) {
    selStatus.onchange = (e) => {
      STATE_METAS.status = e.target.value;
      renderMetasLinhasTable(data);
    };
  }

  const inSearch = document.getElementById('metasSearch');
  if (inSearch) {
    inSearch.oninput = (e) => {
      STATE_METAS.search = e.target.value;
      renderMetasLinhasTable(data);
    };
  }

  const selSort = document.getElementById('metasSortMode');
  if (selSort) {
    selSort.onchange = (e) => {
      STATE_METAS.sort = e.target.value;
      renderMetasLinhasTable(data);
    };
  }
}

/* ==========================================================================
   ABA 5: METAS POR DIRETORIA & DISTRITAIS (tabMetasDiretoria)
   ========================================================================== */
async function renderMetasDiretoriaTab() {
  const data = await loadMetasData();
  if (!data) return;

  renderDiretoriaCards(data);
  renderRankingDistritais(data);
  populateDiretoriaSelectors(data);
  renderDiretoriaHierarchicalTable(data);
  wireDiretoriaEvents(data);
  _dirRendered = true;
}

function renderDiretoriaCards(data) {
  const container = document.getElementById('diretoriaCardsGrid');
  if (!container) return;

  const diretorias = data.diretorias || [];
  let html = '';

  diretorias.forEach(d => {
    const atingClamped = Math.min(100, Math.max(0, d.ating_pct));
    const isCintia = d.diretor.toLowerCase().includes('cintia');
    const colorTheme = isCintia ? 'var(--apple-blue)' : 'var(--apple-indigo)';
    const softColor = isCintia ? 'var(--apple-blue-soft)' : 'var(--apple-indigo-soft)';

    html += `
      <div class="diretoria-card" style="border-top: 4px solid ${colorTheme};">
        <div class="diretoria-card-header">
          <div class="diretoria-name">
            <span>👤</span> ${d.diretor}
          </div>
          ${_badgeAting(d.ating_pct)}
        </div>

        <div class="diretoria-meta-kpis">
          <div class="diretoria-kpi-item">
            <div class="lbl">Meta Setembro</div>
            <div class="val" style="color:${colorTheme};">${_fmtRSCompact(d.meta_mensal)}</div>
          </div>
          <div class="diretoria-kpi-item">
            <div class="lbl">Realizado D-1</div>
            <div class="val" style="color:var(--apple-green-text);">${_fmtRSCompact(d.real_acum_dmax)}</div>
          </div>
          <div class="diretoria-kpi-item">
            <div class="lbl">Meta D-1</div>
            <div class="val">${_fmtRSCompact(d.meta_acum_dmax)}</div>
          </div>
          <div class="diretoria-kpi-item">
            <div class="lbl">Desvio D-1</div>
            <div class="val">${_fmtRSSigned(d.desvio_rs)}</div>
          </div>
        </div>

        <div class="diretoria-progress-wrap">
          <div style="display:flex; justify-content:space-between; font-size:11px; font-weight:600; color:var(--text-secondary);">
            <span>Progresso da Meta D-1</span>
            <span>${d.ating_pct.toFixed(1).replace('.', ',')}%</span>
          </div>
          <div class="diretoria-progress-bar">
            <div class="diretoria-progress-fill" style="width:${atingClamped}%; background:${d.ating_pct >= 100 ? 'var(--apple-green)' : colorTheme};"></div>
          </div>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; font-size:11.5px; color:var(--text-tertiary); padding-top:6px; border-top:1px solid var(--border-subtle);">
          <span>🏢 ${d.total_distritais} Distritais subordinados</span>
          <span style="font-weight:600; color:var(--text-secondary);">${d.share_empresa_pct.toFixed(1)}% do faturamento da rede</span>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function renderRankingDistritais(data) {
  const container = document.getElementById('rankingDistritaisBar');
  if (!container) return;

  const distritais = [...(data.distritais || [])].sort((a, b) => b.ating_pct - a.ating_pct);
  let html = '';

  distritais.forEach((dt, idx) => {
    const activeClass = (STATE_DIR.distrital === dt.distrital) ? 'active' : '';
    html += `
      <div class="distrital-rank-pill ${activeClass}" onclick="filterDistritalPill('${dt.distrital}')">
        <div class="name">#${idx + 1} ${_escHtml(dt.distrital)}</div>
        <div class="sub">${dt.diretor}</div>
        <div class="nums">
          <span class="ating" style="color:${dt.ating_pct >= 100 ? 'var(--apple-green-text)' : 'var(--text-primary)'};">${dt.ating_pct.toFixed(1).replace('.', ',')}%</span>
          <span style="font-size:11px; font-weight:600; color:var(--text-secondary);">${_fmtRSCompact(dt.real_acum_dmax)}</span>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function filterDistritalPill(distNome) {
  const selDist = document.getElementById('dirFilterDistrital');
  if (STATE_DIR.distrital === distNome) {
    STATE_DIR.distrital = 'ALL';
    if (selDist) selDist.value = 'ALL';
  } else {
    STATE_DIR.distrital = distNome;
    if (selDist) selDist.value = distNome;
  }
  if (METAS_DATA) {
    renderRankingDistritais(METAS_DATA);
    renderDiretoriaHierarchicalTable(METAS_DATA);
  }
}

function populateDiretoriaSelectors(data) {
  const selDist = document.getElementById('dirFilterDistrital');
  const selGrp = document.getElementById('dirFilterGrupo');
  if (!selDist || !selGrp) return;

  if (selDist.options.length <= 1) {
    const dists = data.distritais || [];
    dists.forEach(d => {
      const opt = document.createElement('option');
      opt.value = d.distrital;
      opt.textContent = `${d.distrital} (${d.diretor})`;
      selDist.appendChild(opt);
    });
  }

  if (selGrp.options.length <= 1) {
    const grupos = data.grupos || [];
    grupos.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.grupo;
      opt.textContent = g.grupo;
      selGrp.appendChild(opt);
    });
  }
}

function renderDiretoriaHierarchicalTable(data) {
  const tbody = document.getElementById('tbodyMetasDiretoria');
  if (!tbody) return;

  const diretorias = data.diretorias || [];
  let html = '';
  let rowCount = 0;

  const q = STATE_DIR.search.trim().toLowerCase();
  const dirFilter = STATE_DIR.diretoria;
  const distFilter = STATE_DIR.distrital;
  const grpFilter = STATE_DIR.grupo;

  diretorias.forEach(dir => {
    if (dirFilter !== 'ALL' && dir.diretor !== dirFilter) return;

    const isDirExpanded = STATE_DIR.expandedDirs.has(dir.diretor) || q.length > 0;
    const dirToggle = isDirExpanded ? '▼' : '▶';

    // Linha Nível 1: Diretoria
    html += `
      <tr class="row-diretoria" onclick="toggleDirTree('dir', '${dir.diretor}')">
        <td class="tree-indent-0" style="position:sticky;left:0;z-index:11;background:inherit;">
          <span class="tree-toggle-icon">${dirToggle}</span>
          <span style="font-weight:800;color:var(--apple-blue);font-size:13.5px;">🏢 DIRETORIA: ${dir.diretor.toUpperCase()}</span>
        </td>
        <td class="num"><span class="apple-tag tag-neu">Diretoria</span></td>
        <td class="num font-weight-600">${_fmtRS(dir.meta_mensal)}</td>
        <td class="num">${_fmtRS(dir.meta_acum_dmax)}</td>
        <td class="num font-weight-600" style="color:var(--apple-blue);">${_fmtRS(dir.real_acum_dmax)}</td>
        <td class="num">${_fmtRSSigned(dir.desvio_rs)}</td>
        <td class="num">${_badgeDesvio(dir.desvio_pct, 'pct')}</td>
        <td class="num">${_badgeAting(dir.ating_pct)}</td>
        <td class="num">${_statusIcon(dir.status)}</td>
      </tr>
    `;
    rowCount++;

    if (!isDirExpanded) return;

    // Nível 2: Distritais
    (dir.distritais || []).forEach(dist => {
      if (distFilter !== 'ALL' && dist.distrital !== distFilter) return;

      const distKey = `${dir.diretor}|${dist.distrital}`;
      const isDistExpanded = STATE_DIR.expandedDists.has(distKey) || q.length > 0;
      const distToggle = isDistExpanded ? '▼' : '▶';

      html += `
        <tr class="row-distrital" onclick="toggleDirTree('dist', '${distKey}')">
          <td class="tree-indent-1" style="position:sticky;left:0;z-index:10;background:inherit;">
            <span class="tree-toggle-icon">${distToggle}</span>
            <span style="font-weight:700;color:var(--text-primary);">📍 Distrital: ${_escHtml(dist.distrital)}</span>
          </td>
          <td class="num"><span class="apple-tag tag-neu" style="color:var(--apple-indigo);background:var(--apple-indigo-soft);">Distrital</span></td>
          <td class="num font-weight-600">${_fmtRS(dist.meta_mensal)}</td>
          <td class="num">${_fmtRS(dist.meta_acum_dmax)}</td>
          <td class="num font-weight-600" style="color:var(--apple-indigo);">${_fmtRS(dist.real_acum_dmax)}</td>
          <td class="num">${_fmtRSSigned(dist.desvio_rs)}</td>
          <td class="num">${_badgeDesvio(dist.desvio_pct, 'pct')}</td>
          <td class="num">${_badgeAting(dist.ating_pct)}</td>
          <td class="num">${_statusIcon(dist.status)}</td>
        </tr>
      `;
      rowCount++;

      if (!isDistExpanded) return;

      // Nível 3: Grupos dentro do Distrital
      (dist.grupos || []).forEach(grp => {
        if (grpFilter !== 'ALL' && grp.grupo !== grpFilter) return;

        const grpKey = `${distKey}|${grp.grupo}`;
        const isGrpExpanded = STATE_DIR.expandedGrupos.has(grpKey) || q.length > 0;
        const grpToggle = isGrpExpanded ? '▼' : '▶';

        html += `
          <tr class="row-metas-grupo" onclick="toggleDirTree('grp', '${grpKey}')">
            <td class="tree-indent-2" style="position:sticky;left:0;z-index:9;background:inherit;">
              <span class="tree-toggle-icon">${grpToggle}</span>
              <span style="font-weight:600;color:var(--text-secondary);">📦 ${_escHtml(grp.grupo)}</span>
            </td>
            <td class="num"><span class="apple-tag tag-neu">Grupo</span></td>
            <td class="num font-weight-600">${_fmtRS(grp.meta_mensal)}</td>
            <td class="num">${_fmtRS(grp.meta_acum_dmax)}</td>
            <td class="num font-weight-600">${_fmtRS(grp.real_acum_dmax)}</td>
            <td class="num">${_fmtRSSigned(grp.desvio_rs)}</td>
            <td class="num">${_badgeDesvio(grp.desvio_pct, 'pct')}</td>
            <td class="num">${_badgeAting(grp.ating_pct)}</td>
            <td class="num">${_statusIcon(grp.status)}</td>
          </tr>
        `;
        rowCount++;

        if (!isGrpExpanded) return;

        // Nível 4: Linhas de Produtos dentro do Grupo
        (grp.linhas || []).forEach(lin => {
          if (q.length > 0 && !lin.linha.toLowerCase().includes(q) && !(lin.familia && lin.familia.toLowerCase().includes(q))) {
            return;
          }

          html += `
            <tr class="row-metas-linha">
              <td class="tree-indent-3" style="position:sticky;left:0;z-index:8;background:#FFFFFF;">
                <span style="color:var(--text-tertiary);margin-right:6px;">•</span>
                <span style="color:var(--text-primary);">${_escHtml(lin.linha)}</span>
                ${lin.subgrupo ? `<span style="font-size:10px;color:var(--text-tertiary);margin-left:6px;">(${_escHtml(lin.subgrupo)})</span>` : ''}
              </td>
              <td class="num" style="color:var(--text-tertiary);font-size:11px;">Linha</td>
              <td class="num">${_fmtRS(lin.meta_mensal)}</td>
              <td class="num">${_fmtRS(lin.meta_acum_dmax)}</td>
              <td class="num font-weight-600" style="color:var(--apple-blue);">${_fmtRS(lin.real_acum_dmax)}</td>
              <td class="num">${_fmtRSSigned(lin.desvio_rs)}</td>
              <td class="num">${_badgeDesvio(lin.desvio_pct, 'pct')}</td>
              <td class="num">${_badgeAting(lin.ating_pct)}</td>
              <td class="num">${_statusIcon(lin.status)}</td>
            </tr>
          `;
          rowCount++;
        });
      });
    });
  });

  tbody.innerHTML = html || '<tr><td colspan="9" style="text-align:center;padding:24px;color:var(--text-tertiary);">Nenhum registro encontrado com os filtros selecionados.</td></tr>';

  const countBadge = document.getElementById('dirTableCount');
  if (countBadge) countBadge.textContent = `${rowCount} itens visíveis na árvore`;
}

function toggleDirTree(type, key) {
  if (type === 'dir') {
    if (STATE_DIR.expandedDirs.has(key)) STATE_DIR.expandedDirs.delete(key);
    else STATE_DIR.expandedDirs.add(key);
  } else if (type === 'dist') {
    if (STATE_DIR.expandedDists.has(key)) STATE_DIR.expandedDists.delete(key);
    else STATE_DIR.expandedDists.add(key);
  } else if (type === 'grp') {
    if (STATE_DIR.expandedGrupos.has(key)) STATE_DIR.expandedGrupos.delete(key);
    else STATE_DIR.expandedGrupos.add(key);
  }
  if (METAS_DATA) renderDiretoriaHierarchicalTable(METAS_DATA);
}

function wireDiretoriaEvents(data) {
  const selDir = document.getElementById('dirFilterDiretoria');
  if (selDir) {
    selDir.onchange = (e) => {
      STATE_DIR.diretoria = e.target.value;
      renderDiretoriaHierarchicalTable(data);
    };
  }

  const selDist = document.getElementById('dirFilterDistrital');
  if (selDist) {
    selDist.onchange = (e) => {
      STATE_DIR.distrital = e.target.value;
      renderRankingDistritais(data);
      renderDiretoriaHierarchicalTable(data);
    };
  }

  const selGrp = document.getElementById('dirFilterGrupo');
  if (selGrp) {
    selGrp.onchange = (e) => {
      STATE_DIR.grupo = e.target.value;
      renderDiretoriaHierarchicalTable(data);
    };
  }

  const inSearch = document.getElementById('dirSearch');
  if (inSearch) {
    inSearch.oninput = (e) => {
      STATE_DIR.search = e.target.value;
      renderDiretoriaHierarchicalTable(data);
    };
  }

  const btnExpDist = document.getElementById('btnDirExpandDist');
  if (btnExpDist) {
    btnExpDist.onclick = () => {
      (data.distritais || []).forEach(d => STATE_DIR.expandedDists.add(`${d.diretor}|${d.distrital}`));
      renderDiretoriaHierarchicalTable(data);
    };
  }

  const btnExpGrp = document.getElementById('btnDirExpandGrupos');
  if (btnExpGrp) {
    btnExpGrp.onclick = () => {
      (data.diretorias || []).forEach(dir => {
        STATE_DIR.expandedDirs.add(dir.diretor);
        (dir.distritais || []).forEach(dt => {
          const distKey = `${dir.diretor}|${dt.distrital}`;
          STATE_DIR.expandedDists.add(distKey);
          (dt.grupos || []).forEach(g => STATE_DIR.expandedGrupos.add(`${distKey}|${g.grupo}`));
        });
      });
      renderDiretoriaHierarchicalTable(data);
    };
  }

  const btnExpAll = document.getElementById('btnDirExpandAll');
  if (btnExpAll) {
    btnExpAll.onclick = () => {
      (data.diretorias || []).forEach(dir => {
        STATE_DIR.expandedDirs.add(dir.diretor);
        (dir.distritais || []).forEach(dt => {
          const distKey = `${dir.diretor}|${dt.distrital}`;
          STATE_DIR.expandedDists.add(distKey);
          (dt.grupos || []).forEach(g => STATE_DIR.expandedGrupos.add(`${distKey}|${g.grupo}`));
        });
      });
      renderDiretoriaHierarchicalTable(data);
    };
  }

  const btnCollapse = document.getElementById('btnDirCollapseAll');
  if (btnCollapse) {
    btnCollapse.onclick = () => {
      STATE_DIR.expandedDirs.clear();
      STATE_DIR.expandedDists.clear();
      STATE_DIR.expandedGrupos.clear();
      renderDiretoriaHierarchicalTable(data);
    };
  }
}
