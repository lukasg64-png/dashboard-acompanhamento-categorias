/* waterfall.js — v3 — Dynamic Waterfall with Pivot-Table Controls & Meta Comparison */

let waterfallChart = null;

/* ── Waterfall State ────────────────────────────────── */
const WF = {
  dimension: 'categoria',  // categoria, subgrupo, linha, laboratorio, canal_agregado, canal, diretor, distrital
  comparison: 'mom',        // mom, yoy, meta
  metric: 'total',          // total, digital, dt
  sort: 'impacto',          // impacto, ganho_rs, queda_rs, crescimento, queda, alpha
  limit: 20
};

const DIM_LABELS = {
  categoria: 'Categorias',
  subgrupo: 'Subgrupos',
  linha: 'Linhas',
  diretor: 'Diretorias',
  distrital: 'Distritais',
  canal_agregado: 'Canais (Agrupado)',
  canal: 'Canais (Detalhado)'
};

const METRIC_LABELS = {
  total: 'Venda Total',
  digital: 'Venda Digital',
  dt: 'Digital + Tele'
};

const CANAL_GROUPS = {
  'Loja Física': ['Venda Balcão', 'Venda Caixa', 'Credito Facil', 'Auto Atendimento', 'Recarga'],
  'Venda Digital': ['APP', 'iFood', 'SITE', 'APP Tele Entrega', 'SITE Tele Entrega', 'e_Commerce', 'Rappi'],
  'Televendas': ['Venda Tele Entrega', 'Tele Encaminhada Lojas', 'Venda Tele Entrega Central', 'Tele Vizinhança']
};

/* ── Init ────────────────────────────────────────────── */
function initWaterfall() {
  // Tab navigation Apple Style
  const tabBtns = document.querySelectorAll('#mainTabNav .apple-tab-btn, #mainTabNav .tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.dataset.tab;
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      const target = document.getElementById(tabId);
      if (target) target.classList.add('active');
      if (tabId === 'tabWaterfall') triggerWaterfall();
      if (tabId === 'tabMetasSetembro' && typeof renderMetasSetembroTab === 'function') renderMetasSetembroTab();
      if (tabId === 'tabMetasDiretoria' && typeof renderMetasDiretoriaTab === 'function') renderMetasDiretoriaTab();
    });
  });

  // Pill bar: Dimension
  wireupPillBar('wfDimension', 'dim', val => { WF.dimension = val; triggerWaterfall(); });
  // Pill bar: Comparison
  wireupPillBar('wfComparison', 'comp', val => { WF.comparison = val; triggerWaterfall(); });
  // Pill bar: Metric
  wireupPillBar('wfMetric', 'metric', val => { WF.metric = val; triggerWaterfall(); });

  // Select: Sort
  const sortSel = document.getElementById('wfSort');
  if (sortSel) sortSel.addEventListener('change', e => { WF.sort = e.target.value; triggerWaterfall(); });

  // Select: Limit
  const limitSel = document.getElementById('wfLimit');
  if (limitSel) limitSel.addEventListener('change', e => { WF.limit = parseInt(e.target.value) || 20; triggerWaterfall(); });
}

function wireupPillBar(containerId, dataAttr, callback) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.querySelectorAll('.segmented-btn, .wf-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      container.querySelectorAll('.segmented-btn, .wf-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      callback(btn.dataset[dataAttr]);
    });
  });
}

function triggerWaterfall() {
  updateConfigSummary();
  renderWaterfall();
}

/* ── Config Summary Tags ─────────────────────────────── */
function updateConfigSummary() {
  const el = document.getElementById('wfConfigSummary');
  if (!el) return;

  const isSetembro = (typeof STATE === 'undefined' || STATE.mesReferencia === 'setembro');
  const isMeta = WF.comparison === 'meta';
  const curLabel = isMeta ? 'Realizado D-1' : (isSetembro ? 'Set/26' : 'Ago/26');
  const compLabel = isMeta
    ? 'Meta Acum. D-1'
    : (WF.comparison === 'mom'
        ? (isSetembro ? 'Ago/26' : 'Jul/26')
        : (isSetembro ? 'Set/25' : 'Ago/25'));

  const compText = isMeta
    ? `Vs Meta: ${compLabel} → ${curLabel}`
    : (WF.comparison === 'mom' ? `MoM: ${compLabel} → ${curLabel}` : `YoY: ${compLabel} → ${curLabel}`);

  // Active sidebar filters
  let filterTags = '';
  if (typeof STATE !== 'undefined') {
    if (STATE.diretores && STATE.diretores.size > 0) filterTags += tag('👤', `Diretor: ${Array.from(STATE.diretores).join(', ')}`);
    if (STATE.distritais && STATE.distritais.size > 0) filterTags += tag('📍', `Distrital: ${Array.from(STATE.distritais).join(', ')}`);
    if (STATE.grupos && STATE.grupos.size > 0) filterTags += tag('📦', `Grupo: ${Array.from(STATE.grupos).join(', ')}`);
    if (STATE.grupoCanal && STATE.grupoCanal !== 'ALL') filterTags += tag('🏪', `Canal: ${STATE.grupoCanal}`);
  }

  el.innerHTML = `
    ${tag('📐', DIM_LABELS[WF.dimension] || 'Categorias')}
    ${tag('⚡', compText)}
    ${tag('💰', METRIC_LABELS[WF.metric] || 'Faturamento Total')}
    ${tag('🔀', document.getElementById('wfSort')?.options[document.getElementById('wfSort')?.selectedIndex]?.text || WF.sort)}
    ${tag('📊', 'Top ' + WF.limit)}
    ${filterTags}
  `;
}

function tag(icon, text) {
  return `<span class="wf-config-tag"><span class="tag-icon">${icon}</span>${text}</span>`;
}

/* ── Get Waterfall Data ──────────────────────────────── */
function getWaterfallData() {
  const isSetembro = (typeof STATE === 'undefined' || STATE.mesReferencia === 'setembro');
  const isMeta = WF.comparison === 'meta';
  const curLabel = isMeta ? 'Realizado D-1' : (isSetembro ? 'Set/26' : 'Ago/26');
  const isMom = WF.comparison === 'mom';
  const compLabel = isMeta
    ? 'Meta Acum. D-1'
    : (isMom
        ? (isSetembro ? 'Ago/26' : 'Jul/26')
        : (isSetembro ? 'Set/25' : 'Ago/25'));

  let items = [];
  let title = '';

  const dimLabel = DIM_LABELS[WF.dimension] || 'Categorias';
  const compType = isMeta ? 'Vs Meta' : (isMom ? 'MoM' : 'YoY');
  title = `${dimLabel}: ${compLabel} → ${curLabel} (${compType}) — ${METRIC_LABELS[WF.metric] || 'Faturamento Total'}`;

  if (isMeta) {
    const metasData = (typeof _METAS_SETEMBRO !== 'undefined' && _METAS_SETEMBRO) ? _METAS_SETEMBRO : ((typeof METAS_DATA !== 'undefined' && METAS_DATA) ? METAS_DATA : null);
    
    if (WF.dimension === 'categoria') {
      let grupos = metasData?.grupos || [];
      if (typeof STATE !== 'undefined' && STATE.grupos && STATE.grupos.size > 0) {
        grupos = grupos.filter(g => STATE.grupos.has(g.grupo));
      }
      items = grupos.map(g => ({
        label: cleanGroupName(g.grupo),
        current: g.real_acum_dmax || 0,
        base: g.meta_acum_dmax || 0
      }));
    } else if (WF.dimension === 'subgrupo') {
      let linhas = metasData?.linhas || [];
      if (typeof STATE !== 'undefined' && STATE.grupos && STATE.grupos.size > 0) {
        linhas = linhas.filter(l => STATE.grupos.has(l.grupo));
      }
      const map = {};
      linhas.forEach(l => {
        const key = cleanGroupName(l.subgrupo || l.familia || 'Outros');
        if (!map[key]) map[key] = { current: 0, base: 0 };
        map[key].current += (l.real_acum_dmax || 0);
        map[key].base += (l.meta_acum_dmax || 0);
      });
      items = Object.entries(map).map(([label, v]) => ({ label, current: v.current, base: v.base }));
    } else if (WF.dimension === 'linha') {
      let linhas = metasData?.linhas || [];
      if (typeof STATE !== 'undefined' && STATE.grupos && STATE.grupos.size > 0) {
        linhas = linhas.filter(l => STATE.grupos.has(l.grupo));
      }
      items = linhas.map(l => ({
        label: l.linha,
        current: l.real_acum_dmax || 0,
        base: l.meta_acum_dmax || 0
      }));
    } else if (WF.dimension === 'diretor') {
      let diretorias = metasData?.diretorias || [];
      if (typeof STATE !== 'undefined' && STATE.diretores && STATE.diretores.size > 0) {
        diretorias = diretorias.filter(d => STATE.diretores.has(d.diretor));
      }
      items = diretorias.map(d => ({
        label: d.diretor,
        current: d.real_acum_dmax || 0,
        base: d.meta_acum_dmax || 0
      }));
    } else if (WF.dimension === 'distrital') {
      let distritais = metasData?.distritais || [];
      if (typeof STATE !== 'undefined' && STATE.diretores && STATE.diretores.size > 0) {
        distritais = distritais.filter(d => STATE.diretores.has(d.diretoria));
      }
      items = distritais.map(d => ({
        label: d.distrital,
        current: d.real_acum_dmax || 0,
        base: d.meta_acum_dmax || 0
      }));
    } else if (WF.dimension === 'canal_agregado') {
      items = buildCanaisAgregados(true);
      title = `Canais (Agrupado): Realizado D-1 vs Base Anterior (Canais não possuem meta orçamentária)`;
    } else if (WF.dimension === 'canal') {
      items = buildCanaisDetalhado(true);
      title = `Canais (Detalhado): Realizado D-1 vs Base Anterior (Canais não possuem meta orçamentária)`;
    } else {
      // Fallback para dimensões sem meta direta
      const grupos = metasData?.grupos || [];
      items = grupos.map(g => ({
        label: cleanGroupName(g.grupo),
        current: g.real_acum_dmax || 0,
        base: g.meta_acum_dmax || 0
      }));
    }
  } else {
    // Choose value fields based on metric
    const curField = WF.metric === 'digital' ? 'venda_digital_jul_26' : WF.metric === 'dt' ? 'venda_dt_jul_26' : 'venda_jul_26';
    const momField = WF.metric === 'digital' ? 'venda_digital_jun_26' : WF.metric === 'dt' ? 'venda_dt_jun_26' : 'venda_jun_26';
    const yoyField = WF.metric === 'digital' ? 'venda_digital_jul_25' : WF.metric === 'dt' ? 'venda_dt_jul_25' : 'venda_jul_25';
    const baseField = isMom ? momField : yoyField;

    switch (WF.dimension) {
      case 'categoria':
        items = buildFromGrupos(curField, baseField);
        break;
      case 'subgrupo':
        items = buildFromHierField('subgrupo', curField, baseField);
        break;
      case 'linha':
        items = buildFromHierField('linha', curField, baseField);
        break;
      case 'diretor':
        items = buildFromCatField('diretor', curField, baseField);
        break;
      case 'distrital':
        items = buildFromCatField('distrital', curField, baseField);
        break;
      case 'canal_agregado':
        items = buildCanaisAgregados(isMom);
        break;
      case 'canal':
        items = buildCanaisDetalhado(isMom);
        break;
    }
  }

  // Calculate delta
  items = items.map(item => ({
    ...item,
    delta: item.current - item.base,
    deltaPct: item.base > 0 ? ((item.current / item.base) - 1) * 100 : (item.current > 0 ? 100 : 0)
  })).filter(i => Math.abs(i.delta) > 0.01);

  // Sort
  switch (WF.sort) {
    case 'impacto':
      items.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
      break;
    case 'ganho_rs':
    case 'desvio_rs_pos':
      items.sort((a, b) => b.delta - a.delta);
      break;
    case 'queda_rs':
    case 'desvio_rs_neg':
      items.sort((a, b) => a.delta - b.delta);
      break;
    case 'crescimento':
    case 'desvio_pct_pos':
      items.sort((a, b) => (b.deltaPct) - (a.deltaPct));
      break;
    case 'queda':
    case 'desvio_pct_neg':
      items.sort((a, b) => (a.deltaPct) - (b.deltaPct));
      break;
    case 'alpha':
      items.sort((a, b) => a.label.localeCompare(b.label));
      break;
  }

  // Limit
  if (WF.limit < 50 && items.length > WF.limit) items = items.slice(0, WF.limit);

  const totalBase = items.reduce((s, i) => s + i.base, 0);
  const totalCurrent = items.reduce((s, i) => s + i.current, 0);
  const totalDelta = totalCurrent - totalBase;
  const totalDeltaPct = totalBase > 0 ? ((totalCurrent / totalBase) - 1) * 100 : 0;

  return { items, title, totalBase, totalCurrent, totalDelta, totalDeltaPct, curLabel, compLabel };
}

/* ── Data Builders ───────────────────────────────────── */

function buildFromGrupos(curField, baseField) {
  const grupos = (typeof getFilteredGrupos === 'function') ? getFilteredGrupos() : [];
  return grupos.map(g => ({
    label: cleanGroupName(g.grupo),
    current: g[curField] || 0,
    base: g[baseField] || 0
  }));
}

function buildFromHierField(field, curField, baseField) {
  const hier = getFilteredHierData();
  const map = {};
  hier.forEach(c => {
    const key = c[field] || '';
    if (!key) return;
    if (!map[key]) map[key] = { current: 0, base: 0 };
    map[key].current += (c[curField] || 0);
    map[key].base += (c[baseField] || 0);
  });
  return Object.entries(map).map(([label, v]) => ({ label: cleanGroupName(label), current: v.current, base: v.base }));
}

function buildFromCatField(field, curField, baseField) {
  const hier = getFilteredHierData();
  const map = {};
  hier.forEach(c => {
    const key = c[field] || '';
    if (!key) return;
    if (!map[key]) map[key] = { current: 0, base: 0 };
    map[key].current += (c[curField] || 0);
    map[key].base += (c[baseField] || 0);
  });
  return Object.entries(map).map(([label, v]) => ({ label: cleanGroupName(label), current: v.current, base: v.base }));
}

function buildCanaisAgregados(isMom) {
  const canais = (typeof getFilteredCanaisList === 'function') ? getFilteredCanaisList() : (DATA.canais || []);
  const maxDia = (DATA.kpis?.periodo_info?.dias_fechados) || (typeof STATE !== 'undefined' && STATE.mesReferencia === 'agosto' ? 19 : 3);
  const defaultEnd = (typeof STATE !== 'undefined' && STATE.mesReferencia === 'agosto') ? maxDia : 31;
  const useDays = typeof STATE !== 'undefined' && (STATE.startDay !== 1 || STATE.endDay < defaultEnd);

  // Build group map
  const canalToGroup = {};
  Object.entries(CANAL_GROUPS).forEach(([grp, members]) => {
    members.forEach(m => { canalToGroup[m] = grp; });
  });

  const map = {};
  canais.forEach(c => {
    const grp = canalToGroup[c.canal] || 'Outros Canais';
    if (!map[grp]) map[grp] = { current: 0, base: 0 };

    let curVal, baseVal;
    if (useDays && c.d26_07) {
      curVal = sumDays(c.d26_07, STATE.startDay, STATE.endDay);
      baseVal = isMom
        ? (c.d26_06 ? sumDays(c.d26_06, STATE.startDay, STATE.endDay) : 0)
        : (c.d25 ? sumDays(c.d25, STATE.startDay, STATE.endDay) : 0);
    } else {
      curVal = c.venda_jul_26 != null ? c.venda_jul_26 : (c.v26 || 0);
      baseVal = isMom
        ? (c.venda_jun_26 != null ? c.venda_jun_26 : (c.v26_06 || 0))
        : (c.venda_jul_25 != null ? c.venda_jul_25 : (c.v25 || 0));
    }

    map[grp].current += curVal;
    map[grp].base += baseVal;
  });

  return Object.entries(map).map(([label, v]) => ({ label, current: v.current, base: v.base }));
}

function buildCanaisDetalhado(isMom) {
  const canais = (typeof getFilteredCanaisList === 'function') ? getFilteredCanaisList() : (DATA.canais || []);
  const maxDia = (DATA.kpis?.periodo_info?.dias_fechados) || (typeof STATE !== 'undefined' && STATE.mesReferencia === 'agosto' ? 19 : 3);
  const defaultEnd = (typeof STATE !== 'undefined' && STATE.mesReferencia === 'agosto') ? maxDia : 31;
  const useDays = typeof STATE !== 'undefined' && (STATE.startDay !== 1 || STATE.endDay < defaultEnd);

  return canais.map(c => {
    let curVal, baseVal;
    if (useDays && c.d26_07) {
      curVal = sumDays(c.d26_07, STATE.startDay, STATE.endDay);
      baseVal = isMom
        ? (c.d26_06 ? sumDays(c.d26_06, STATE.startDay, STATE.endDay) : 0)
        : (c.d25 ? sumDays(c.d25, STATE.startDay, STATE.endDay) : 0);
    } else {
      curVal = c.venda_jul_26 != null ? c.venda_jul_26 : (c.v26 || 0);
      baseVal = isMom
        ? (c.venda_jun_26 != null ? c.venda_jun_26 : (c.v26_06 || 0))
        : (c.venda_jul_25 != null ? c.venda_jul_25 : (c.v25 || 0));
    }
    return { label: c.canal, current: curVal, base: baseVal };
  });
}

function getFilteredHierData() {
  if (typeof getFilteredHier === 'function') return getFilteredHier();
  return DATA.hierarquia || [];
}

/* ── Helpers ─────────────────────────────────────────── */
function cleanGroupName(name) {
  if (!name) return '';
  return name.replace(/\(\d+\)$/, '').trim();
}

function wfFmtCompact(val) {
  if (typeof fmtCompact === 'function') return fmtCompact(val);
  const abs = Math.abs(val);
  if (abs >= 1e9) return 'R$ ' + (val / 1e9).toFixed(1).replace('.', ',') + ' Bi';
  if (abs >= 1e6) return 'R$ ' + (val / 1e6).toFixed(1).replace('.', ',') + ' Mi';
  if (abs >= 1e3) return 'R$ ' + Math.round(val / 1e3).toLocaleString('pt-BR') + ' mil';
  return 'R$ ' + Math.round(val).toLocaleString('pt-BR');
}

function wfFmtPct(val) {
  const sign = val >= 0 ? '+' : '';
  return sign + val.toFixed(1).replace('.', ',') + '%';
}

function wfTagPct(val) {
  if (typeof tagPct === 'function') return tagPct(val);
  const cls = val > 0 ? 'pos' : val < 0 ? 'neg' : 'neu';
  return `<span class="badge ${cls}">${wfFmtPct(val)}</span>`;
}

/* ── Render KPIs ─────────────────────────────────────── */
function renderWaterfallKPIs(data) {
  const kpiRow = document.getElementById('wfKpiRow');
  if (!kpiRow) return;

  const isMeta = WF.comparison === 'meta';
  const baseTitle = isMeta ? 'META ACUM. D-1' : `FATURAMENTO BASE (${esc(data.compLabel)})`;
  const baseSub = isMeta ? 'Meta esperada acumulada' : 'Período comparativo base';
  const finalTitle = isMeta ? 'REALIZADO D-1' : `FATURAMENTO FINAL (${esc(data.curLabel)})`;
  const finalSub = isMeta ? 'Total acumulado até D-1' : 'Total do período atual';
  const varTitle = isMeta ? 'DESVIO TOTAL' : 'VARIAÇÃO TOTAL';
  const varSub = isMeta ? 'vs meta esperada' : 'vs base';
  const growerTitle = isMeta ? 'MAIOR SUPERÁVIT' : 'MAIOR CRESCIMENTO';
  const fallerTitle = isMeta ? 'MAIOR DÉFICIT' : 'MAIOR QUEDA';

  const deltaColor = data.totalDelta >= 0 ? '#16a34a' : '#dc2626';
  const deltaSign = data.totalDelta >= 0 ? '+' : '';
  const deltaCls = data.totalDelta >= 0 ? 'accent-green' : 'accent-red';
  const topGrower = data.items.filter(i => i.delta > 0).sort((a, b) => b.deltaPct - a.deltaPct)[0];
  const topFaller = data.items.filter(i => i.delta < 0).sort((a, b) => a.deltaPct - b.deltaPct)[0];

  kpiRow.innerHTML = `
    <div class="apple-kpi-card accent-blue">
      <div class="kpi-card-header">
        <span class="kpi-card-title">${baseTitle}</span>
      </div>
      <div class="kpi-value-main">${wfFmtCompact(data.totalBase)}</div>
      <div class="kpi-sub-value">${baseSub}</div>
    </div>
    <div class="apple-kpi-card ${deltaCls}">
      <div class="kpi-card-header">
        <span class="kpi-card-title">${varTitle}</span>
      </div>
      <div class="kpi-value-main" style="color: ${deltaColor};">${deltaSign}${wfFmtCompact(data.totalDelta)}</div>
      <div class="kpi-footer-deltas">
        <span class="apple-tag ${data.totalDelta >= 0 ? 'tag-pos' : 'tag-neg'}">${wfFmtPct(data.totalDeltaPct)}</span>
        <span class="sublabel">${varSub}</span>
      </div>
    </div>
    <div class="apple-kpi-card accent-indigo">
      <div class="kpi-card-header">
        <span class="kpi-card-title">${finalTitle}</span>
      </div>
      <div class="kpi-value-main">${wfFmtCompact(data.totalCurrent)}</div>
      <div class="kpi-sub-value">${finalSub}</div>
    </div>
    <div class="apple-kpi-card accent-green">
      <div class="kpi-card-header">
        <span class="kpi-card-title">${growerTitle}</span>
      </div>
      <div class="kpi-value-main" style="font-size:16px; color:var(--apple-green-text);">${topGrower ? esc(topGrower.label) : '—'}</div>
      <div class="kpi-sub-value">${topGrower ? '+' + wfFmtCompact(topGrower.delta) : ''} (${topGrower ? wfFmtPct(topGrower.deltaPct) : ''})</div>
    </div>
    <div class="apple-kpi-card accent-red">
      <div class="kpi-card-header">
        <span class="kpi-card-title">${fallerTitle}</span>
      </div>
      <div class="kpi-value-main" style="font-size:16px; color:var(--apple-red-text);">${topFaller ? esc(topFaller.label) : '—'}</div>
      <div class="kpi-sub-value">${topFaller ? wfFmtCompact(topFaller.delta) : ''} (${topFaller ? wfFmtPct(topFaller.deltaPct) : ''})</div>
    </div>
  `;
}

/* ── Render Detail Table ─────────────────────────────── */
function renderWaterfallTable(data) {
  const thead = document.getElementById('wfDetailThead');
  const tbody = document.getElementById('wfDetailTbody');
  if (!thead || !tbody) return;

  const isMeta = WF.comparison === 'meta';
  const colBase = isMeta ? 'Meta D-1' : data.compLabel;
  const colCur = isMeta ? 'Realizado D-1' : data.curLabel;
  const colDelta = isMeta ? 'Desvio R$' : 'Var. R$';
  const colPct = isMeta ? 'Desvio %' : 'Var. %';

  thead.innerHTML = `<tr>
    <th class="col-name">#</th>
    <th class="col-name">${DIM_LABELS[WF.dimension] || 'Dimensão'}</th>
    <th class="col-num">${colBase}</th>
    <th class="col-num">${colCur}</th>
    <th class="col-num">${colDelta}</th>
    <th class="col-num">${colPct}</th>
    <th class="col-num">Impacto %</th>
  </tr>`;

  const totalDelta = Math.abs(data.totalDelta) || 1;

  tbody.innerHTML = data.items.map((item, i) => {
    const impacto = (item.delta / totalDelta * 100);
    const cls = item.delta >= 0 ? 'pos' : 'neg';
    return `<tr>
      <td style="color:var(--text-3); font-size:11px; text-align:center; width:30px;">${i + 1}</td>
      <td class="col-name" style="font-weight:600;">${item.label}</td>
      <td class="col-num">${typeof fmtRS === 'function' ? fmtRS(item.base) : wfFmtCompact(item.base)}</td>
      <td class="col-num">${typeof fmtRS === 'function' ? fmtRS(item.current) : wfFmtCompact(item.current)}</td>
      <td class="col-num"><span class="badge ${cls}" style="font-size:11px;">${item.delta >= 0 ? '+' : ''}${wfFmtCompact(item.delta)}</span></td>
      <td class="col-num"><span class="badge ${cls}" style="font-size:11px;">${wfFmtPct(item.deltaPct)}</span></td>
      <td class="col-num" style="font-size:11px; color:var(--text-2);">${impacto >= 0 ? '+' : ''}${impacto.toFixed(1).replace('.', ',')}%</td>
    </tr>`;
  }).join('');
}

/* ── Render Waterfall Chart ──────────────────────────── */
function renderWaterfall() {
  const data = getWaterfallData();
  const wrap = document.getElementById('wfChartWrap');
  if (!wrap) return;

  // Ensure canvas exists (might have been replaced by empty message)
  if (!wrap.querySelector('canvas')) {
    wrap.innerHTML = '<canvas id="chartWaterfall"></canvas>';
  }
  const canvas = document.getElementById('chartWaterfall');
  if (!canvas) return;

  // Render KPIs and table
  renderWaterfallKPIs(data);
  renderWaterfallTable(data);

  if (data.items.length === 0) {
    if (waterfallChart) { waterfallChart.destroy(); waterfallChart = null; }
    wrap.innerHTML = '<div class="wf-empty">Sem dados para esta configuração</div>';
    return;
  }

  // Build chart data
  const labels = [data.compLabel, ...data.items.map(i => i.label), data.curLabel];
  const baseVal = data.totalBase;
  let running = baseVal;

  const barData = [];
  const bgColors = [];
  const borderColors = [];

  // Base bar
  barData.push([0, baseVal]);
  bgColors.push('#475569');
  borderColors.push('#334155');

  // Delta bars
  data.items.forEach(item => {
    const start = running;
    running += item.delta;
    if (item.delta >= 0) {
      barData.push([start, running]);
      bgColors.push('#22c55e');
      borderColors.push('#16a34a');
    } else {
      barData.push([running, start]);
      bgColors.push('#ef4444');
      borderColors.push('#dc2626');
    }
  });

  // Total bar
  barData.push([0, data.totalCurrent]);
  bgColors.push('#475569');
  borderColors.push('#334155');

  // Running values for connectors
  const runningValues = [baseVal];
  { let r = baseVal; data.items.forEach(item => { r += item.delta; runningValues.push(r); }); runningValues.push(data.totalCurrent); }

  // Connector plugin
  const connectorPlugin = {
    id: 'waterfallConnector',
    afterDatasetDraw(chart) {
      const { ctx } = chart;
      const meta = chart.getDatasetMeta(0);
      ctx.save();
      ctx.strokeStyle = '#94a3b8';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      for (let i = 0; i < meta.data.length - 1; i++) {
        if (i + 1 === meta.data.length - 1) continue;
        const curr = meta.data[i];
        const next = meta.data[i + 1];
        const runVal = runningValues[i + 1];
        const yLine = chart.scales.y.getPixelForValue(runVal);
        ctx.beginPath();
        ctx.moveTo(curr.x + curr.width / 2, yLine);
        ctx.lineTo(next.x - next.width / 2, yLine);
        ctx.stroke();
      }
      ctx.restore();
    }
  };

  // Labels plugin
  const labelsPlugin = {
    id: 'waterfallLabels',
    afterDatasetDraw(chart) {
      const { ctx } = chart;
      const meta = chart.getDatasetMeta(0);
      ctx.save();
      ctx.font = '600 10px Inter';
      ctx.textAlign = 'center';
      meta.data.forEach((bar, idx) => {
        const d = barData[idx];
        const isTotal = (idx === 0 || idx === labels.length - 1);
        let displayVal, yPos, color;
        if (isTotal) {
          displayVal = wfFmtCompact(d[1]);
          yPos = bar.y - 8;
          color = '#334155';
        } else {
          const item = data.items[idx - 1];
          displayVal = (item.delta >= 0 ? '+' : '') + wfFmtCompact(item.delta);
          if (item.delta >= 0) {
            yPos = chart.scales.y.getPixelForValue(Math.max(d[0], d[1])) - 8;
            color = '#15803d';
          } else {
            yPos = chart.scales.y.getPixelForValue(Math.min(d[0], d[1])) - 8;
            color = '#b91c1c';
          }
        }
        ctx.fillStyle = color;
        ctx.fillText(displayVal, bar.x, yPos);
      });
      ctx.restore();
    }
  };

  if (waterfallChart) waterfallChart.destroy();

  const isMeta = WF.comparison === 'meta';

  waterfallChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: barData,
        backgroundColor: bgColors,
        borderColor: borderColors,
        borderWidth: 1,
        borderRadius: 4,
        borderSkipped: false,
        barPercentage: 0.75,
        categoryPercentage: 0.85
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 500, easing: 'easeOutQuart' },
      layout: { padding: { top: 30, bottom: 10 } },
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: data.title,
          font: { family: 'Outfit', size: 14, weight: '700' },
          color: '#1a1d23',
          padding: { bottom: 12 }
        },
        tooltip: {
          backgroundColor: '#1e293b',
          titleFont: { family: 'Inter', size: 13, weight: '700' },
          bodyFont: { family: 'Inter', size: 12 },
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            title: ctx => ctx[0].label,
            label: ctx => {
              const idx = ctx.dataIndex;
              const d = barData[idx];
              if (idx === 0) return isMeta ? `Total Meta D-1: R$ ${Math.round(d[1]).toLocaleString('pt-BR')}` : `Total Base: R$ ${Math.round(d[1]).toLocaleString('pt-BR')}`;
              if (idx === labels.length - 1) return isMeta ? `Total Realizado D-1: R$ ${Math.round(d[1]).toLocaleString('pt-BR')}` : `Total Atual: R$ ${Math.round(d[1]).toLocaleString('pt-BR')}`;
              const item = data.items[idx - 1];
              return [
                `${isMeta ? 'Realizado' : 'Atual'}: R$ ${Math.round(item.current).toLocaleString('pt-BR')}`,
                `${isMeta ? 'Meta D-1' : 'Base'}: R$ ${Math.round(item.base).toLocaleString('pt-BR')}`,
                `${isMeta ? 'Desvio R$' : 'Var'}: ${item.delta >= 0 ? '+' : ''}R$ ${Math.round(item.delta).toLocaleString('pt-BR')}`,
                `${isMeta ? 'Desvio %' : 'Var %'}: ${wfFmtPct(item.deltaPct)}`
              ];
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { family: 'Inter', size: 10, weight: '600' },
            color: '#5a6070',
            maxRotation: 45,
            minRotation: 0,
            autoSkip: false
          }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
          ticks: {
            font: { family: 'Inter', size: 11 },
            color: '#8b90a0',
            callback: v => {
              if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(1) + ' Bi';
              if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(0) + ' Mi';
              if (Math.abs(v) >= 1e3) return (v / 1e3).toFixed(0) + ' mil';
              return v;
            }
          }
        }
      }
    },
    plugins: [connectorPlugin, labelsPlugin]
  });
}

/* ── Hook into app.js lifecycle ─────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initWaterfall();
});
