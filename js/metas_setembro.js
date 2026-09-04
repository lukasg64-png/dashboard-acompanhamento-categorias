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
  sort: 'meta_mensal',
  chartMode: 'diario' // 'diario' ou 'acumulado'
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
  return 'R$ ' + Math.round(Math.abs(v)).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function _fmtRSCompact(v) {
  if (v === null || v === undefined || isNaN(v)) return '-';
  const val = Math.abs(v);
  if (val >= 1e9) return 'R$ ' + (val / 1e9).toFixed(1).replace('.', ',') + ' B';
  if (val >= 1e6) return 'R$ ' + (val / 1e6).toFixed(1).replace('.', ',') + ' M';
  if (val >= 1e3) return 'R$ ' + Math.round(val / 1e3).toLocaleString('pt-BR') + ' mil';
  return 'R$ ' + Math.round(val).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function _fmtRSSigned(v) {
  if (v === null || v === undefined || isNaN(v)) return '-';
  const prefix = v > 0 ? '+' : v < 0 ? '-' : '';
  return prefix + ' R$ ' + Math.round(Math.abs(v)).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
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

function _cleanGroupName(name) {
  if (!name) return '';
  return name.replace(/\(\d+\)$/, '').trim();
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
   MOTOR DE FILTRAGEM UNIFICADO DINÂMICO PARA METAS SETEMBRO
   Garante que filtros laterais e locais agreguem números exatos em tempo real
   ========================================================================== */
function getFilteredMetasModel(data, tab = 'macro') {
  if (!data) return null;

  // 1. Resolução de filtros ativos
  let activeDiretores = null;
  if (tab === 'diretoria' && STATE_DIR.diretoria !== 'ALL') {
    activeDiretores = new Set([STATE_DIR.diretoria]);
  } else if (typeof STATE !== 'undefined' && STATE.diretores && STATE.diretores.size > 0) {
    activeDiretores = STATE.diretores;
  }

  let activeDistritais = null;
  if (tab === 'diretoria' && STATE_DIR.distrital !== 'ALL') {
    activeDistritais = new Set([STATE_DIR.distrital]);
  } else if (typeof STATE !== 'undefined' && STATE.distritais && STATE.distritais.size > 0) {
    activeDistritais = STATE.distritais;
  }

  let activeGrupos = null;
  if (tab === 'macro') {
    if (STATE_METAS.categoria !== 'ALL') {
      activeGrupos = new Set([STATE_METAS.categoria]);
    } else if (typeof STATE !== 'undefined' && STATE.grupos && STATE.grupos.size > 0) {
      activeGrupos = STATE.grupos;
    }
  } else {
    if (STATE_DIR.grupo !== 'ALL') {
      activeGrupos = new Set([STATE_DIR.grupo]);
    } else if (typeof STATE !== 'undefined' && STATE.grupos && STATE.grupos.size > 0) {
      activeGrupos = STATE.grupos;
    }
  }

  const activeSubgrupos = (typeof STATE !== 'undefined' && STATE.subgrupos && STATE.subgrupos.size > 0) ? STATE.subgrupos : null;
  const activeLinhas = (typeof STATE !== 'undefined' && STATE.linhas && STATE.linhas.size > 0) ? STATE.linhas : null;

  const searchQuery = (tab === 'macro'
    ? (STATE_METAS.search || (typeof STATE !== 'undefined' ? STATE.search : ''))
    : (STATE_DIR.search || (typeof STATE !== 'undefined' ? STATE.search : ''))
  ).trim().toLowerCase();

  const statusFilter = (tab === 'macro' ? STATE_METAS.status : 'ALL');

  const excluirTipo = (typeof STATE !== 'undefined' ? STATE.excluirTipo : 'NONE');
  const excluirValor = (typeof STATE !== 'undefined' ? STATE.excluirValor : 'NONE');

  // 2. Travessia e agregação
  const filteredDiretorias = [];
  const survivingLinhas = [];
  const mapGrupos = {};

  (data.diretorias || []).forEach(dire => {
    if (activeDiretores && !activeDiretores.has(dire.diretor)) return;

    const filteredDistritais = [];
    (dire.distritais || []).forEach(dist => {
      if (activeDistritais && !activeDistritais.has(dist.distrital)) return;

      const filteredGrpList = [];
      (dist.grupos || []).forEach(grp => {
        if (activeGrupos && !activeGrupos.has(grp.grupo)) return;
        if (excluirTipo === 'grupo' && excluirValor !== 'NONE' && grp.grupo === excluirValor) return;

        const filteredLinList = [];
        (grp.linhas || []).forEach(lin => {
          if (activeSubgrupos && !activeSubgrupos.has(lin.subgrupo)) return;
          if (activeLinhas && !activeLinhas.has(lin.linha)) return;
          if (excluirTipo === 'subgrupo' && excluirValor !== 'NONE' && lin.subgrupo === excluirValor) return;
          if (excluirTipo === 'linha' && excluirValor !== 'NONE' && lin.linha === excluirValor) return;

          if (searchQuery.length > 0) {
            const match = lin.linha.toLowerCase().includes(searchQuery) ||
                          (lin.familia && lin.familia.toLowerCase().includes(searchQuery)) ||
                          (lin.subgrupo && lin.subgrupo.toLowerCase().includes(searchQuery)) ||
                          grp.grupo.toLowerCase().includes(searchQuery) ||
                          dist.distrital.toLowerCase().includes(searchQuery);
            if (!match) return;
          }

          if (statusFilter !== 'ALL' && lin.status !== statusFilter) return;

          filteredLinList.push(lin);
          survivingLinhas.push({
            ...lin,
            grupo: grp.grupo,
            distrital: dist.distrital,
            diretor: dire.diretor
          });

          // Agregar por Grupo
          if (!mapGrupos[grp.grupo]) {
            mapGrupos[grp.grupo] = {
              grupo: grp.grupo,
              meta_mensal: 0,
              meta_acum_dmax: 0,
              real_acum_dmax: 0,
              total_linhas: new Set()
            };
          }
          mapGrupos[grp.grupo].meta_mensal += (lin.meta_mensal || 0);
          mapGrupos[grp.grupo].meta_acum_dmax += (lin.meta_acum_dmax || 0);
          mapGrupos[grp.grupo].real_acum_dmax += (lin.real_acum_dmax || 0);
          mapGrupos[grp.grupo].total_linhas.add(lin.linha);
        });

        if (filteredLinList.length > 0) {
          const m_m = filteredLinList.reduce((s, l) => s + l.meta_mensal, 0);
          const m_d = filteredLinList.reduce((s, l) => s + l.meta_acum_dmax, 0);
          const r_d = filteredLinList.reduce((s, l) => s + l.real_acum_dmax, 0);
          const desv = r_d - m_d;
          const atg = m_d > 0 ? (r_d / m_d * 100) : 0;
          filteredGrpList.push({
            ...grp,
            meta_mensal: m_m,
            meta_acum_dmax: m_d,
            real_acum_dmax: r_d,
            desvio_rs: desv,
            desvio_pct: m_d > 0 ? ((r_d / m_d) - 1) * 100 : 0,
            ating_pct: atg,
            status: atg >= 100 ? 'acima' : (atg >= 95 ? 'alerta' : 'abaixo'),
            total_linhas: filteredLinList.length,
            linhas: filteredLinList
          });
        }
      });

      if (filteredGrpList.length > 0) {
        const m_m = filteredGrpList.reduce((s, g) => s + g.meta_mensal, 0);
        const m_d = filteredGrpList.reduce((s, g) => s + g.meta_acum_dmax, 0);
        const r_d = filteredGrpList.reduce((s, g) => s + g.real_acum_dmax, 0);
        const desv = r_d - m_d;
        const atg = m_d > 0 ? (r_d / m_d * 100) : 0;
        filteredDistritais.push({
          ...dist,
          meta_mensal: m_m,
          meta_acum_dmax: m_d,
          real_acum_dmax: r_d,
          desvio_rs: desv,
          desvio_pct: m_d > 0 ? ((r_d / m_d) - 1) * 100 : 0,
          ating_pct: atg,
          status: atg >= 100 ? 'acima' : (atg >= 95 ? 'alerta' : 'abaixo'),
          total_linhas: filteredGrpList.reduce((s, g) => s + g.total_linhas, 0),
          grupos: filteredGrpList
        });
      }
    });

    if (filteredDistritais.length > 0) {
      const m_m = filteredDistritais.reduce((s, d) => s + d.meta_mensal, 0);
      const m_d = filteredDistritais.reduce((s, d) => s + d.meta_acum_dmax, 0);
      const r_d = filteredDistritais.reduce((s, d) => s + d.real_acum_dmax, 0);
      const desv = r_d - m_d;
      const atg = m_d > 0 ? (r_d / m_d * 100) : 0;
      filteredDiretorias.push({
        ...dire,
        meta_mensal: m_m,
        meta_acum_dmax: m_d,
        real_acum_dmax: r_d,
        desvio_rs: desv,
        desvio_pct: m_d > 0 ? ((r_d / m_d) - 1) * 100 : 0,
        ating_pct: atg,
        status: atg >= 100 ? 'acima' : (atg >= 95 ? 'alerta' : 'abaixo'),
        total_distritais: filteredDistritais.length,
        distritais: filteredDistritais
      });
    }
  });

  // 3. Totais calculados do escopo filtrado
  const meta_mensal = survivingLinhas.reduce((s, l) => s + l.meta_mensal, 0);
  const meta_acum_dmax = survivingLinhas.reduce((s, l) => s + l.meta_acum_dmax, 0);
  const real_acum_dmax = survivingLinhas.reduce((s, l) => s + l.real_acum_dmax, 0);
  const desvio_rs = real_acum_dmax - meta_acum_dmax;
  const desvio_pct = meta_acum_dmax > 0 ? ((real_acum_dmax / meta_acum_dmax) - 1) * 100 : 0;
  const ating_pct = meta_acum_dmax > 0 ? (real_acum_dmax / meta_acum_dmax) * 100 : 0;
  const dMax = data.d_max || 3;
  const projecao_runrate = dMax > 0 ? (real_acum_dmax / dMax) * 30 : 0;

  // 4. Etiqueta de contexto visual
  const parts = [];
  if (activeDiretores && activeDiretores.size > 0) parts.push(`Diretoria: ${Array.from(activeDiretores).join(', ')}`);
  if (activeDistritais && activeDistritais.size > 0) parts.push(`Distrital: ${Array.from(activeDistritais).join(', ')}`);
  if (activeGrupos && activeGrupos.size > 0) parts.push(`Grupo: ${Array.from(activeGrupos).map(_cleanGroupName).join(', ')}`);
  if (activeLinhas && activeLinhas.size > 0) parts.push(`${activeLinhas.size} Linha(s)`);
  if (searchQuery) parts.push(`Busca: "${searchQuery}"`);
  const contextLabel = parts.length > 0 ? parts.join(' • ') : 'Total Empresa';

  const empresa = {
    meta_mensal,
    meta_acum_dmax,
    real_acum_dmax,
    desvio_rs,
    desvio_pct,
    ating_pct,
    projecao_runrate,
    status: ating_pct >= 100 ? 'acima' : (ating_pct >= 95 ? 'alerta' : 'abaixo'),
    contextLabel,
    hasFilters: parts.length > 0
  };

  // Grupos consolidados
  const totalShareMeta = meta_mensal || 1;
  const grupos = Object.values(mapGrupos).map(g => {
    const desv = g.real_acum_dmax - g.meta_acum_dmax;
    const atg = g.meta_acum_dmax > 0 ? (g.real_acum_dmax / g.meta_acum_dmax * 100) : 0;
    return {
      grupo: g.grupo,
      meta_mensal: g.meta_mensal,
      share_meta: (g.meta_mensal / totalShareMeta) * 100,
      meta_acum_dmax: g.meta_acum_dmax,
      real_acum_dmax: g.real_acum_dmax,
      desvio_rs: desv,
      desvio_pct: g.meta_acum_dmax > 0 ? ((g.real_acum_dmax / g.meta_acum_dmax) - 1) * 100 : 0,
      ating_pct: atg,
      total_linhas: g.total_linhas.size,
      status: atg >= 100 ? 'acima' : (atg >= 95 ? 'alerta' : 'abaixo')
    };
  }).sort((a, b) => b.meta_mensal - a.meta_mensal);

  // Linhas agregadas únicas
  const mapUniqueLinhas = {};
  survivingLinhas.forEach(l => {
    if (!mapUniqueLinhas[l.linha]) {
      mapUniqueLinhas[l.linha] = {
        linha: l.linha,
        familia: l.familia,
        subgrupo: l.subgrupo,
        grupo: l.grupo,
        meta_mensal: 0,
        meta_acum_dmax: 0,
        real_acum_dmax: 0
      };
    }
    mapUniqueLinhas[l.linha].meta_mensal += (l.meta_mensal || 0);
    mapUniqueLinhas[l.linha].meta_acum_dmax += (l.meta_acum_dmax || 0);
    mapUniqueLinhas[l.linha].real_acum_dmax += (l.real_acum_dmax || 0);
  });

  const uniqueLinhas = Object.values(mapUniqueLinhas).map(l => {
    const desv = l.real_acum_dmax - l.meta_acum_dmax;
    const atg = l.meta_acum_dmax > 0 ? (l.real_acum_dmax / l.meta_acum_dmax * 100) : 0;
    return {
      ...l,
      desvio_rs: desv,
      desvio_pct: l.meta_acum_dmax > 0 ? ((l.real_acum_dmax / l.meta_acum_dmax) - 1) * 100 : 0,
      ating_pct: atg,
      status: atg >= 100 ? 'acima' : (atg >= 95 ? 'alerta' : 'abaixo')
    };
  });

  // Lista plana de distritais sobreviventes
  const distritais = [];
  filteredDiretorias.forEach(d => {
    d.distritais.forEach(dt => distritais.push(dt));
  });

  return {
    ...data,
    empresa,
    grupos,
    linhas: uniqueLinhas,
    diretorias: filteredDiretorias,
    distritais
  };
}

/* ── Sincronizadores de controles de UI ─────────────────── */
function syncMetasMacroInputs(rawData) {
  const selCat = document.getElementById('metasFilterCategoria');
  if (selCat) {
    if (typeof STATE !== 'undefined' && STATE.grupos && STATE.grupos.size === 1) {
      const gVal = Array.from(STATE.grupos)[0];
      if (STATE_METAS.categoria !== gVal) {
        STATE_METAS.categoria = gVal;
        selCat.value = gVal;
      }
    } else if (typeof STATE !== 'undefined' && STATE.grupos && STATE.grupos.size === 0) {
      if (STATE_METAS.categoria !== 'ALL' && (!selCat.value || selCat.value === 'ALL')) {
        STATE_METAS.categoria = 'ALL';
        selCat.value = 'ALL';
      }
    }
  }

  const inSearch = document.getElementById('metasSearch');
  if (inSearch && typeof STATE !== 'undefined' && STATE.search) {
    if (inSearch.value !== STATE.search) {
      STATE_METAS.search = STATE.search;
      inSearch.value = STATE.search;
    }
  }
}

function syncMetasDiretoriaInputs(rawData) {
  const selDir = document.getElementById('dirFilterDiretoria');
  if (selDir && typeof STATE !== 'undefined') {
    if (STATE.diretores && STATE.diretores.size === 1) {
      const dVal = Array.from(STATE.diretores)[0];
      if (STATE_DIR.diretoria !== dVal) {
        STATE_DIR.diretoria = dVal;
        selDir.value = dVal;
      }
    } else if (STATE.diretores && STATE.diretores.size === 0) {
      if (STATE_DIR.diretoria !== 'ALL' && (!selDir.value || selDir.value === 'ALL')) {
        STATE_DIR.diretoria = 'ALL';
        selDir.value = 'ALL';
      }
    }
  }

  const selDt = document.getElementById('dirFilterDistrital');
  if (selDt && typeof STATE !== 'undefined') {
    if (STATE.distritais && STATE.distritais.size === 1) {
      const dtVal = Array.from(STATE.distritais)[0];
      if (STATE_DIR.distrital !== dtVal) {
        STATE_DIR.distrital = dtVal;
        selDt.value = dtVal;
      }
    } else if (STATE.distritais && STATE.distritais.size === 0) {
      if (STATE_DIR.distrital !== 'ALL' && (!selDt.value || selDt.value === 'ALL')) {
        STATE_DIR.distrital = 'ALL';
        selDt.value = 'ALL';
      }
    }
  }

  const selGrp = document.getElementById('dirFilterGrupo');
  if (selGrp && typeof STATE !== 'undefined') {
    if (STATE.grupos && STATE.grupos.size === 1) {
      const gVal = Array.from(STATE.grupos)[0];
      if (STATE_DIR.grupo !== gVal) {
        STATE_DIR.grupo = gVal;
        selGrp.value = gVal;
      }
    } else if (STATE.grupos && STATE.grupos.size === 0) {
      if (STATE_DIR.grupo !== 'ALL' && (!selGrp.value || selGrp.value === 'ALL')) {
        STATE_DIR.grupo = 'ALL';
        selGrp.value = 'ALL';
      }
    }
  }

  const inDirSearch = document.getElementById('dirSearch');
  if (inDirSearch && typeof STATE !== 'undefined' && STATE.search) {
    if (inDirSearch.value !== STATE.search) {
      STATE_DIR.search = STATE.search;
      inDirSearch.value = STATE.search;
    }
  }
}

/* ==========================================================================
   ABA 4: MACRO EMPRESA & CATEGORIAS (tabMetasSetembro)
   ========================================================================== */
async function renderMetasSetembroTab() {
  const rawData = await loadMetasData();
  if (!rawData) return;

  syncMetasMacroInputs(rawData);
  const model = getFilteredMetasModel(rawData, 'macro');

  renderMetasKPIs(model);
  renderMetasChart(model, rawData);
  renderMetasGruposEmpresa(model);
  renderMetasLinhasTable(model);
  wireMetasMacroEvents(rawData);
  _metasRendered = true;
}

function renderMetasKPIs(model) {
  const strip = document.getElementById('kpiStripMetas');
  if (!strip) return;

  const emp = model.empresa || {};
  const dMax = model.d_max || 3;
  const diasRestantes = model.dias_restantes || 27;
  const necDiaria = Math.max(0, (emp.meta_mensal - emp.real_acum_dmax) / Math.max(1, diasRestantes));

  const scopeBadge = emp.hasFilters
    ? `<span class="apple-tag tag-pos" style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${_escHtml(emp.contextLabel)}">🎯 ${_escHtml(emp.contextLabel)}</span>`
    : `<span class="apple-tag tag-neu">Total Empresa</span>`;

  strip.innerHTML = `
    <!-- Card 1: Meta Mensal -->
    <div class="apple-kpi-card accent-blue">
      <div class="kpi-card-header">
        <span class="kpi-card-title">META SETEMBRO/2026</span>
        ${scopeBadge}
      </div>
      <div class="kpi-value-main" style="color:var(--apple-blue);">${_fmtRSCompact(emp.meta_mensal)}</div>
      <div class="kpi-sub-value">${_fmtRS(emp.meta_mensal)} orçado</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">${emp.hasFilters ? 'Escopo filtrado ativo' : 'Alocação Distrital × Linhas'}</span>
      </div>
    </div>

    <!-- Card 2: Meta Esperada D-1 -->
    <div class="apple-kpi-card accent-indigo">
      <div class="kpi-card-header">
        <span class="kpi-card-title">META ACUM. ATÉ D-1</span>
        <span class="apple-tag tag-neu">Dia ${dMax} de 30</span>
      </div>
      <div class="kpi-value-main" style="color:var(--apple-indigo);">${_fmtRSCompact(emp.meta_acum_dmax)}</div>
      <div class="kpi-sub-value">${_fmtRS(emp.meta_acum_dmax)} esperado</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">${(dMax / 30 * 100).toFixed(1)}% do mês decorrido</span>
      </div>
    </div>

    <!-- Card 3: Realizado D-1 -->
    <div class="apple-kpi-card accent-green">
      <div class="kpi-card-header">
        <span class="kpi-card-title">REALIZADO D-1 QLIK</span>
        <span class="apple-tag tag-pos">Resultado</span>
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
        <span class="sublabel">Baseado na média diária</span>
      </div>
    </div>

    <!-- Card 6: Dias Restantes -->
    <div class="apple-kpi-card accent-teal">
      <div class="kpi-card-header">
        <span class="kpi-card-title">DIAS RESTANTES</span>
        <span class="apple-tag tag-neu">Setembro</span>
      </div>
      <div class="kpi-value-main" style="color:var(--apple-teal);">${diasRestantes} dias</div>
      <div class="kpi-sub-value">Necessário: ${_fmtRSCompact(necDiaria)}/dia</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">Para 100% da meta</span>
      </div>
    </div>
  `;
}

// Plugin customizado para desenhar badges numéricos com % de desvio em cada dia
const metasDesvioDataLabelsPlugin = {
  id: 'metasDesvioDataLabels',
  afterDatasetsDraw(chart, args, options) {
    const { ctx } = chart;
    const datasets = chart.data.datasets;
    const desvioDatasetIndex = datasets.findIndex(ds => ds.isDesvioLine);
    if (desvioDatasetIndex === -1) return;

    const dataset = datasets[desvioDatasetIndex];
    const meta = chart.getDatasetMeta(desvioDatasetIndex);
    if (!meta || !meta.data) return;

    ctx.save();
    meta.data.forEach((element, index) => {
      const val = dataset.data[index];
      if (val === null || val === undefined || isNaN(val)) return;

      const isPositive = val >= 0;
      const text = (isPositive ? '+' : '') + Number(val).toFixed(1).replace('.', ',') + '%';
      const bgColor = isPositive ? '#34C759' : '#FF3B30';

      ctx.font = 'bold 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      const textMetrics = ctx.measureText(text);
      const textWidth = textMetrics.width;
      const paddingX = 7;
      const pillHeight = 20;
      const pillWidth = textWidth + paddingX * 2;
      const pillRadius = 5;

      const x = element.x;
      const yOffset = -22;
      const y = Math.max(12, element.y + yOffset);
      const pillX = x - pillWidth / 2;
      const pillY = y - pillHeight / 2;

      ctx.shadowColor = 'rgba(0, 0, 0, 0.2)';
      ctx.shadowBlur = 4;
      ctx.shadowOffsetY = 2;

      ctx.fillStyle = bgColor;
      ctx.beginPath();
      if (typeof ctx.roundRect === 'function') {
        ctx.roundRect(pillX, pillY, pillWidth, pillHeight, pillRadius);
      } else {
        ctx.rect(pillX, pillY, pillWidth, pillHeight);
      }
      ctx.fill();

      ctx.shadowColor = 'transparent';
      ctx.shadowBlur = 0;
      ctx.shadowOffsetY = 0;

      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.fillStyle = '#FFFFFF';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(text, x, y);
    });
    ctx.restore();
  }
};

function renderMetasChart(model, rawData) {
  const canvas = document.getElementById('chartMetasEvolucao');
  if (!canvas) return;

  const emp = model.empresa || {};
  const baseEmp = (rawData && rawData.empresa) ? rawData.empresa : emp;
  const curva = (rawData && rawData.curva_diaria) ? rawData.curva_diaria : [];
  const dMax = model.d_max || 3;
  const isDiario = STATE_METAS.chartMode !== 'acumulado';

  const titleEl = document.getElementById('metasChartTitle');
  const subtitleEl = document.getElementById('metasEvolucaoSubtitle');
  if (titleEl) {
    titleEl.textContent = isDiario
      ? `Acompanhamento Diário — Venda vs Meta & % Desvio (${emp.contextLabel || 'Total Empresa'})`
      : `Evolução Acumulada MTD — Meta vs Realizado (${emp.contextLabel || 'Total Empresa'})`;
  }
  if (subtitleEl) {
    subtitleEl.textContent = isDiario
      ? 'Setembro/2026 • Barras de Faturamento Diário + Traço com % de Desvio (Verde/Vermelho)'
      : 'Setembro/2026 • Curva diária acumulada ponderada';
  }

  if (_metasChart) _metasChart.destroy();

  const ratioMeta = (baseEmp.meta_mensal > 0) ? (emp.meta_mensal / baseEmp.meta_mensal) : 1;
  const ratioReal = (baseEmp.real_acum_dmax > 0) ? (emp.real_acum_dmax / baseEmp.real_acum_dmax) : 1;

  if (isDiario) {
    const labels = curva.map(c => `Dia ${c.dia} (${c.dia_semana ? c.dia_semana.slice(0, 3) : ''})`);

    const metaDiaria = curva.map((c, i) => {
      const val = c.meta_dia || (baseEmp.evolucao_meta_diaria ? baseEmp.evolucao_meta_diaria[i] : 0);
      return val * ratioMeta;
    });

    const realDiario = curva.map((c, i) => {
      if (i >= dMax) return null;
      const val = c.real_dia !== undefined ? c.real_dia : (baseEmp.evolucao_real_diaria ? baseEmp.evolucao_real_diaria[i] : null);
      return val != null ? val * ratioReal : null;
    });

    const desvioPct = curva.map((c, i) => {
      if (i >= dMax) return null;
      const r = realDiario[i];
      const m = metaDiaria[i];
      if (!m || m <= 0 || r === null) return 0;
      return Number(((r / m - 1.0) * 100.0).toFixed(2));
    });

    const vendaColors = curva.map((c, i) => {
      if (i >= dMax) return 'rgba(0,0,0,0)';
      const d = desvioPct[i];
      return d >= 0 ? 'rgba(52, 199, 89, 0.85)' : 'rgba(255, 59, 48, 0.85)';
    });

    const vendaBorderColors = curva.map((c, i) => {
      if (i >= dMax) return 'rgba(0,0,0,0)';
      const d = desvioPct[i];
      return d >= 0 ? '#248A3D' : '#D70015';
    });

    const pointBgColors = curva.map((c, i) => {
      if (i >= dMax) return 'transparent';
      const d = desvioPct[i];
      return d >= 0 ? '#34C759' : '#FF3B30';
    });

    _metasChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            type: 'bar',
            label: 'Meta do Dia R$',
            data: metaDiaria,
            backgroundColor: 'rgba(0, 113, 227, 0.18)',
            borderColor: 'rgba(0, 113, 227, 0.65)',
            borderWidth: 1.5,
            borderRadius: 6,
            yAxisID: 'y',
            order: 3
          },
          {
            type: 'bar',
            label: 'Venda do Dia R$',
            data: realDiario,
            backgroundColor: vendaColors,
            borderColor: vendaBorderColors,
            borderWidth: 1.5,
            borderRadius: 6,
            yAxisID: 'y',
            order: 2
          },
          {
            type: 'line',
            label: '% Desvio (Venda / Meta - 1)',
            data: desvioPct,
            borderColor: '#8E8E93',
            borderDash: [5, 4],
            borderWidth: 2,
            tension: 0.2,
            pointRadius: 6,
            pointHoverRadius: 9,
            pointBackgroundColor: pointBgColors,
            pointBorderColor: '#FFFFFF',
            pointBorderWidth: 2.5,
            yAxisID: 'y1',
            order: 1,
            isDesvioLine: true
          }
        ]
      },
      plugins: [metasDesvioDataLabelsPlugin],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'top',
            labels: { boxWidth: 12, font: { weight: 600, size: 12 } }
          },
          tooltip: {
            backgroundColor: 'rgba(28, 28, 30, 0.95)',
            titleFont: { size: 13, weight: 'bold' },
            bodyFont: { size: 12 },
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              title: (items) => {
                const idx = items[0].dataIndex;
                const c = curva[idx] || {};
                return `Dia ${c.dia}/09/2026 (${c.dia_semana || ''})`;
              },
              label: (ctx) => {
                const idx = ctx.dataIndex;
                const r = realDiario[idx];
                const m = metaDiaria[idx];
                const d = desvioPct[idx];

                if (ctx.dataset.yAxisID === 'y1') {
                  if (d === null || d === undefined) return ' % Desvio: Aguardando dados';
                  const icon = d >= 0 ? '🟢 Bateu a meta' : '🔴 Abaixo da meta';
                  return ` % Desvio: ${(d >= 0 ? '+' : '')}${d.toFixed(2).replace('.', ',')}% (${icon})`;
                } else if (ctx.dataset.label.includes('Venda')) {
                  if (idx >= dMax || r === null || r === 0) return ' Venda do Dia: Aguardando fechamento';
                  return ` Venda Realizada: R$ ${Math.round(r).toLocaleString('pt-BR')}`;
                } else {
                  return ` Meta do Dia: R$ ${Math.round(m).toLocaleString('pt-BR')}`;
                }
              }
            }
          }
        },
        scales: {
          y: {
            type: 'linear',
            position: 'left',
            ticks: {
              callback: (v) => 'R$ ' + (v / 1e6).toFixed(0) + 'M'
            },
            grid: { color: 'rgba(0,0,0,0.04)' },
            title: { display: true, text: 'Faturamento Diário (R$)', font: { weight: 'bold', size: 11 } }
          },
          y1: {
            type: 'linear',
            position: 'right',
            grid: { drawOnChartArea: false },
            ticks: {
              callback: (v) => (v > 0 ? '+' : '') + v.toFixed(0) + '%'
            },
            title: { display: true, text: '% Desvio (Venda / Meta - 1)', font: { weight: 'bold', size: 11 } }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });

  } else {
    // ── MODO 2: ACUMULADO MTD ──
    const labels = curva.map(c => `Dia ${c.dia}`);
    const metaAcum = curva.map((c, i) => {
      const val = c.meta_acum || (baseEmp.evolucao_meta ? baseEmp.evolucao_meta[i] : 0);
      return val * ratioMeta;
    });
    const realAcum = curva.map((c, i) => {
      if (i >= dMax) return null;
      const val = (baseEmp.evolucao_real && baseEmp.evolucao_real[i] != null) ? baseEmp.evolucao_real[i] : (c.real_acum || null);
      return val != null ? val * ratioReal : null;
    });

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
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12, font: { weight: 600 } } },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: R$ ${Math.round(ctx.raw || 0).toLocaleString('pt-BR')}`
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
}

function renderMetasGruposEmpresa(model) {
  const tbody = document.getElementById('tbodyMetasGruposEmpresa');
  if (!tbody) return;

  const grupos = model.grupos || [];
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

  tbody.innerHTML = html || '<tr><td colspan="10" style="text-align:center;padding:24px;color:var(--text-tertiary);">Nenhum grupo correspondente aos filtros ativos.</td></tr>';

  // Preencher Select de Categorias/Grupos se vazio
  const selCat = document.getElementById('metasFilterCategoria');
  if (selCat && selCat.options.length <= 1) {
    const rawGrupos = (METAS_DATA && METAS_DATA.grupos) ? METAS_DATA.grupos : grupos;
    rawGrupos.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.grupo;
      opt.textContent = g.grupo;
      selCat.appendChild(opt);
    });
  }
}

function renderMetasLinhasTable(model) {
  const tbody = document.getElementById('tbodyMetasLinhas');
  if (!tbody) return;

  let linhas = [...(model.linhas || [])];

  // Ordenação
  switch (STATE_METAS.sort) {
    case 'meta_mensal_desc':
    case 'meta_mensal':
      linhas.sort((a, b) => b.meta_mensal - a.meta_mensal);
      break;
    case 'meta_mensal_asc':
      linhas.sort((a, b) => a.meta_mensal - b.meta_mensal);
      break;
    case 'desvio_rs_pos':
      linhas.sort((a, b) => b.desvio_rs - a.desvio_rs);
      break;
    case 'desvio_rs_neg':
    case 'desvio_rs':
      linhas.sort((a, b) => a.desvio_rs - b.desvio_rs);
      break;
    case 'desvio_pct_pos':
      linhas.sort((a, b) => b.desvio_pct - a.desvio_pct);
      break;
    case 'desvio_pct_neg':
    case 'desvio_pct':
      linhas.sort((a, b) => a.desvio_pct - b.desvio_pct);
      break;
    case 'ating_pct_desc':
    case 'ating_pct':
      linhas.sort((a, b) => b.ating_pct - a.ating_pct);
      break;
    case 'ating_pct_asc':
      linhas.sort((a, b) => a.ating_pct - b.ating_pct);
      break;
    case 'linha_asc':
    case 'linha':
      linhas.sort((a, b) => a.linha.localeCompare(b.linha));
      break;
    case 'linha_desc':
      linhas.sort((a, b) => b.linha.localeCompare(a.linha));
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

function wireMetasMacroEvents(rawData) {
  const btnDiario = document.getElementById('btnMetasChartDiario');
  const btnAcum = document.getElementById('btnMetasChartAcum');
  if (btnDiario && btnAcum) {
    btnDiario.onclick = () => {
      STATE_METAS.chartMode = 'diario';
      btnDiario.classList.add('active');
      btnAcum.classList.remove('active');
      const model = getFilteredMetasModel(rawData, 'macro');
      renderMetasChart(model, rawData);
    };
    btnAcum.onclick = () => {
      STATE_METAS.chartMode = 'acumulado';
      btnAcum.classList.add('active');
      btnDiario.classList.remove('active');
      const model = getFilteredMetasModel(rawData, 'macro');
      renderMetasChart(model, rawData);
    };
  }

  const selCat = document.getElementById('metasFilterCategoria');
  if (selCat) {
    selCat.onchange = (e) => {
      STATE_METAS.categoria = e.target.value;
      renderMetasSetembroTab();
    };
  }

  const selStatus = document.getElementById('metasFilterStatus');
  if (selStatus) {
    selStatus.onchange = (e) => {
      STATE_METAS.status = e.target.value;
      renderMetasSetembroTab();
    };
  }

  const inSearch = document.getElementById('metasSearch');
  if (inSearch) {
    inSearch.oninput = (e) => {
      STATE_METAS.search = e.target.value;
      renderMetasSetembroTab();
    };
  }

  const selSort = document.getElementById('metasSortMode');
  if (selSort) {
    selSort.onchange = (e) => {
      STATE_METAS.sort = e.target.value;
      const model = getFilteredMetasModel(rawData, 'macro');
      renderMetasLinhasTable(model);
    };
  }
}

/* ==========================================================================
   ABA 5: METAS POR DIRETORIA & DISTRITAIS (tabMetasDiretoria)
   ========================================================================== */
async function renderMetasDiretoriaTab() {
  const rawData = await loadMetasData();
  if (!rawData) return;

  syncMetasDiretoriaInputs(rawData);
  const model = getFilteredMetasModel(rawData, 'diretoria');

  renderDiretoriaCards(model);
  renderRankingDistritais(model);
  populateDiretoriaSelectors(rawData, model);
  renderDiretoriaHierarchicalTable(model);
  wireDiretoriaEvents(rawData);
  _dirRendered = true;
}

function renderDiretoriaCards(model) {
  const container = document.getElementById('diretoriaCardsGrid');
  if (!container) return;

  const diretorias = model.diretorias || [];
  let html = '';

  diretorias.forEach(d => {
    const atingClamped = Math.min(100, Math.max(0, d.ating_pct));
    const isCintia = d.diretor.toLowerCase().includes('cintia');
    const colorTheme = isCintia ? 'var(--apple-blue)' : 'var(--apple-indigo)';

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
          <span>🏢 ${d.total_distritais} Distritais exibidos</span>
          <span style="font-weight:600; color:var(--text-secondary);">${d.share_empresa_pct ? d.share_empresa_pct.toFixed(1) + '% da rede' : ''}</span>
        </div>
      </div>
    `;
  });

  container.innerHTML = html || '<div style="padding:20px;color:var(--text-tertiary);text-align:center;grid-column:1/-1;">Nenhuma diretoria selecionada ou correspondente aos filtros.</div>';
}

function renderRankingDistritais(model) {
  const container = document.getElementById('rankingDistritaisBar');
  if (!container) return;

  let distritais = [...(model.distritais || [])];
  distritais.sort((a, b) => b.ating_pct - a.ating_pct);
  let html = '';

  distritais.forEach((dt, idx) => {
    const isSelected = (STATE_DIR.distrital === dt.distrital) || (typeof STATE !== 'undefined' && STATE.distritais && STATE.distritais.has(dt.distrital));
    const activeClass = isSelected ? 'active' : '';
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

  container.innerHTML = html || '<div style="padding:10px 16px;color:var(--text-tertiary);font-size:12px;">Nenhum distrital disponível para os filtros atuais.</div>';
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
  renderMetasDiretoriaTab();
}

function populateDiretoriaDistritais(rawData, model) {
  const selDist = document.getElementById('dirFilterDistrital');
  if (!selDist) return;

  let dists = rawData.distritais || [];
  if (STATE_DIR.diretoria && STATE_DIR.diretoria !== 'ALL') {
    dists = dists.filter(d => d.diretor === STATE_DIR.diretoria);
  }

  selDist.innerHTML = '<option value="ALL">Todos os Distritais</option>';
  dists.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d.distrital;
    opt.textContent = `${d.distrital} (${d.diretor})`;
    if (STATE_DIR.distrital === d.distrital) opt.selected = true;
    selDist.appendChild(opt);
  });
}

function populateDiretoriaSelectors(rawData, model) {
  populateDiretoriaDistritais(rawData, model);
  const selGrp = document.getElementById('dirFilterGrupo');
  if (!selGrp) return;

  if (selGrp.options.length <= 1) {
    const grupos = rawData.grupos || [];
    grupos.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.grupo;
      opt.textContent = g.grupo;
      if (STATE_DIR.grupo === g.grupo) opt.selected = true;
      selGrp.appendChild(opt);
    });
  }
}

function renderDiretoriaHierarchicalTable(model) {
  const tbody = document.getElementById('tbodyMetasDiretoria');
  if (!tbody) return;

  const diretorias = model.diretorias || [];
  let html = '';
  let rowCount = 0;

  const q = STATE_DIR.search.trim().toLowerCase();
  const hasFilterActive = model.empresa?.hasFilters;

  diretorias.forEach(dir => {
    const isDirExpanded = STATE_DIR.expandedDirs.has(dir.diretor) || q.length > 0 || hasFilterActive;
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
      const distKey = `${dir.diretor}|${dist.distrital}`;
      const isDistExpanded = STATE_DIR.expandedDists.has(distKey) || q.length > 0 || hasFilterActive;
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

  tbody.innerHTML = html || '<tr><td colspan="9" style="text-align:center;padding:24px;color:var(--text-tertiary);">Nenhum registro encontrado para a seleção atual.</td></tr>';

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
  renderMetasDiretoriaTab();
}

function wireDiretoriaEvents(rawData) {
  const selDir = document.getElementById('dirFilterDiretoria');
  if (selDir) {
    selDir.onchange = (e) => {
      STATE_DIR.diretoria = e.target.value;
      STATE_DIR.distrital = 'ALL';
      renderMetasDiretoriaTab();
    };
  }

  const selDist = document.getElementById('dirFilterDistrital');
  if (selDist) {
    selDist.onchange = (e) => {
      STATE_DIR.distrital = e.target.value;
      renderMetasDiretoriaTab();
    };
  }

  const selGrp = document.getElementById('dirFilterGrupo');
  if (selGrp) {
    selGrp.onchange = (e) => {
      STATE_DIR.grupo = e.target.value;
      renderMetasDiretoriaTab();
    };
  }

  const inSearch = document.getElementById('dirSearch');
  if (inSearch) {
    inSearch.oninput = (e) => {
      STATE_DIR.search = e.target.value;
      renderMetasDiretoriaTab();
    };
  }

  const btnExpDist = document.getElementById('btnDirExpandDist');
  if (btnExpDist) {
    btnExpDist.onclick = () => {
      (rawData.distritais || []).forEach(d => STATE_DIR.expandedDists.add(`${d.diretor}|${d.distrital}`));
      renderMetasDiretoriaTab();
    };
  }

  const btnExpGrp = document.getElementById('btnDirExpandGrupos');
  if (btnExpGrp) {
    btnExpGrp.onclick = () => {
      (rawData.distritais || []).forEach(d => {
        (d.grupos || []).forEach(g => STATE_DIR.expandedGrupos.add(`${d.diretor}|${d.distrital}|${g.grupo}`));
      });
      renderMetasDiretoriaTab();
    };
  }

  const btnCol = document.getElementById('btnDirCollapseAll');
  if (btnCol) {
    btnCol.onclick = () => {
      STATE_DIR.expandedDirs.clear();
      STATE_DIR.expandedDists.clear();
      STATE_DIR.expandedGrupos.clear();
      renderMetasDiretoriaTab();
    };
  }
}
