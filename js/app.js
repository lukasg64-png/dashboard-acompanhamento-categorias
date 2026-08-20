/* app.js — Acompanhamento de Categorias — v14 (Suporte a Mês de Referência: Agosto Parcial & Julho Fechado) */

let DATA = { kpis: null, canais: [], canaisHier: [], categorias: [], hierarquia: [], filtroHierarquia: {}, filtrosProduto: null };
let STATE = {
  mesReferencia: 'agosto', // 'agosto' ou 'julho'
  diretores: new Set(),
  distritais: new Set(),
  coordenadores: new Set(),
  grupos: new Set(),
  subgrupos: new Set(),
  linhas: new Set(),
  laboratorios: new Set(),
  grupoCanal: 'ALL',
  canalDetalhado: 'ALL',
  excluirTipo: 'NONE',
  excluirValor: 'NONE',
  search: '',
  sort: 'faturamento',
  partMode: 'total_empresa', // 'total_empresa', 'digital_empresa', 'dt_empresa'
  expandedCat: new Set(),
  expandedCh: new Set(['digital', 'digital_tele', 'loja']),
  periodPreset: 'FULL',
  startDay: 1,
  endDay: 31
};

/* ── Loading Overlay Progress Helpers ────────────── */
function updateLoadingProgress(pct, statusText) {
  const bar = document.getElementById('appleLoadingBarFill');
  const txt = document.getElementById('appleLoadingPercent');
  const st = document.getElementById('appleLoadingStatus');
  if (bar) bar.style.width = `${Math.min(100, Math.max(0, pct))}%`;
  if (txt) txt.textContent = `${Math.round(pct)}%`;
  if (st && statusText) st.textContent = statusText;
}

function showLoadingProgress(initialStatus = 'Carregando base analítica...') {
  const overlay = document.getElementById('appleLoadingOverlay');
  if (overlay) {
    overlay.classList.remove('hidden');
    updateLoadingProgress(5, initialStatus);
  }
}

function hideLoadingProgress() {
  updateLoadingProgress(100, 'Tudo pronto!');
  setTimeout(() => {
    const overlay = document.getElementById('appleLoadingOverlay');
    if (overlay) overlay.classList.add('hidden');
  }, 350);
}

document.addEventListener('DOMContentLoaded', async () => {
  showLoadingProgress('Inicializando motor analítico...');
  updateLoadingProgress(15, 'Carregando indicadores corporativos...');
  await loadAllData(STATE.mesReferencia);
  updateLoadingProgress(60, 'Configurando filtros e eventos...');
  wireEvents();
  initMultiSelects();
  updateTableHeaders();
  updateLoadingProgress(85, 'Renderizando visualizações 360°...');
  render();
  updateLoadingProgress(100, 'Pronto!');
  hideLoadingProgress();
});

/* ── Data loading ─────────────────────────────────── */
async function loadAllData(mes = 'agosto') {
  try {
    updateLoadingProgress(25, `Buscando dados de ${mes === 'agosto' ? 'Agosto (D-1 Qlik)' : 'Julho (Fechado)'}...`);
    const prefix = mes === 'agosto' ? 'data/agosto/' : 'data/';
    const urls = [
      prefix + 'executive_kpis.json',
      prefix + 'canais_summary.json',
      prefix + 'canais_by_hierarquia.json',
      prefix + 'categorias_summary.json',
      prefix + 'hierarquia_detalhada.json',
      prefix + 'filtro_hierarquia.json',
      prefix + 'filtros_produto.json',
      prefix + 'clientes_summary.json'
    ];
    const ts = Date.now();
    const results = await Promise.all(urls.map(u => fetch(`${u}?v=${ts}`).then(r => r.json()).catch(() => null)));
    updateLoadingProgress(45, 'Processando hierarquia mercadológica...');
    DATA.kpis = results[0];
    DATA.canais = results[1] || [];
    DATA.canaisHier = results[2] || [];
    DATA.categorias = results[3] || [];
    DATA.hierarquia = results[4] || [];
    DATA.filtroHierarquia = results[5] || {};
    DATA.filtrosProduto = results[6] || null;
    DATA.clientes = results[7] || null;
  } catch (e) { console.error('Erro ao carregar dados:', e); }
}

/* ── Helper para soma de vetores de dias ─────────────── */
function sumDays(arr, startDay, endDay) {
  if (!arr || !arr.length) return 0;
  let s = 0;
  const maxIdx = Math.min(arr.length, endDay);
  for (let i = startDay - 1; i < maxIdx; i++) {
    s += (arr[i] || 0);
  }
  return s;
}


/* ── Events ───────────────────────────────────────── */
function wireEvents() {
  // Month dropdown selector
  const mesSel = sel('filterMesReferencia');
  if (mesSel) {
    mesSel.value = STATE.mesReferencia;
    mesSel.addEventListener('change', async (e) => {
      const month = e.target.value;
      if (STATE.mesReferencia === month) return;
      STATE.mesReferencia = month;

      showLoadingProgress(`Carregando ${month === 'agosto' ? 'Agosto/26 (D-1 Qlik)' : 'Julho/26 (Fechado)'}...`);

      // Reset filters
      STATE.diretores.clear();
      STATE.distritais.clear();
      STATE.coordenadores.clear();
      STATE.grupos.clear();
      STATE.subgrupos.clear();
      STATE.linhas.clear();
      STATE.laboratorios.clear();
      STATE.expandedCat.clear();
      STATE.search = '';
      if (sel('globalSearch')) sel('globalSearch').value = '';

      STATE.startDay = 1;
      STATE.endDay = 31;

      // Load data
      await loadAllData(STATE.mesReferencia);
      updateLoadingProgress(80, 'Atualizando filtros...');
      populateAllMultiSelects();
      updateTableHeaders();
      updateLoadingProgress(95, 'Renderizando tabelas e gráficos...');
      render();
      hideLoadingProgress();
    });
  }

  // Month button handler (Apple segmented control)
  const monthBtns = document.querySelectorAll('#monthSelector .segmented-btn, #monthSelector .month-btn');
  monthBtns.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const month = btn.dataset.month;
      if (STATE.mesReferencia === month) return;
      STATE.mesReferencia = month;
      if (mesSel) mesSel.value = month;
      monthBtns.forEach(b => b.classList.toggle('active', b.dataset.month === month));

      showLoadingProgress(`Carregando ${month === 'agosto' ? 'Agosto/26 (D-1 Qlik)' : 'Julho/26 (Fechado)'}...`);

      STATE.diretores.clear();
      STATE.distritais.clear();
      STATE.coordenadores.clear();
      STATE.grupos.clear();
      STATE.subgrupos.clear();
      STATE.linhas.clear();
      STATE.laboratorios.clear();
      STATE.expandedCat.clear();
      STATE.search = '';
      if (sel('globalSearch')) sel('globalSearch').value = '';

      STATE.startDay = 1;
      STATE.endDay = 31;

      await loadAllData(STATE.mesReferencia);
      updateLoadingProgress(80, 'Atualizando filtros...');
      populateAllMultiSelects();
      updateTableHeaders();
      updateLoadingProgress(95, 'Renderizando tabelas e gráficos...');
      render();
      hideLoadingProgress();
    });
  });

  const presetSel = sel('filterPeriodoPreset');
  if (presetSel) {
    presetSel.addEventListener('change', e => {
      STATE.periodPreset = e.target.value;
      const customBox = sel('customDaysRange');
      if (STATE.periodPreset === 'FULL') {
        STATE.startDay = 1; STATE.endDay = 31;
        if (customBox) customBox.style.display = 'none';
      } else if (STATE.periodPreset === 'MTD_15') {
        STATE.startDay = 1; STATE.endDay = 15;
        if (customBox) customBox.style.display = 'none';
      } else if (STATE.periodPreset === 'MTD_20') {
        STATE.startDay = 1; STATE.endDay = 20;
        if (customBox) customBox.style.display = 'none';
      } else if (STATE.periodPreset === 'CUSTOM') {
        if (customBox) customBox.style.display = 'flex';
        STATE.startDay = parseInt(sel('filterStartDay').value) || 1;
        STATE.endDay = parseInt(sel('filterEndDay').value) || 31;
      }
      STATE.expandedCat.clear(); render();
    });
  }

  const sDay = sel('filterStartDay');
  if (sDay) sDay.addEventListener('change', e => {
    STATE.startDay = Math.max(1, Math.min(31, parseInt(e.target.value) || 1)); render();
  });

  const eDay = sel('filterEndDay');
  if (eDay) eDay.addEventListener('change', e => {
    STATE.endDay = Math.max(1, Math.min(31, parseInt(e.target.value) || 31)); render();
  });

  // Exclusion filter handlers (Filtro Negativo / Excluir)
  const excTipoSel = sel('filterExcluirTipo');
  const excValBox = sel('boxExcluirValor');
  const excValSel = sel('filterExcluirValor');

  if (excTipoSel && excValSel) {
    excTipoSel.addEventListener('change', e => {
      STATE.excluirTipo = e.target.value;
      STATE.excluirValor = 'NONE';

      if (STATE.excluirTipo === 'NONE') {
        if (excValBox) excValBox.style.display = 'none';
        render();
      } else {
        if (excValBox) excValBox.style.display = 'block';
        populateExclusionValues();
      }
    });

    excValSel.addEventListener('change', e => {
      STATE.excluirValor = e.target.value;
      STATE.expandedCat.clear(); render();
    });
  }

  // Channel filters
  const grpCanalSel = sel('filterGrupoCanal');
  const canalDetSel = sel('filterCanalDetalhado');

  if (grpCanalSel) {
    grpCanalSel.addEventListener('change', e => {
      STATE.grupoCanal = e.target.value;
      if (canalDetSel) {
        canalDetSel.value = 'ALL';
        STATE.canalDetalhado = 'ALL';
      }
      if (STATE.grupoCanal === 'digital') {
        STATE.partMode = 'digital_empresa';
      } else if (STATE.grupoCanal === 'digital_tele' || STATE.grupoCanal === 'tele') {
        STATE.partMode = 'dt_empresa';
      } else {
        STATE.partMode = 'total_empresa';
      }
      updatePartTabsUI();
      STATE.expandedCat.clear(); render();
    });
  }

  if (canalDetSel) {
    canalDetSel.addEventListener('change', e => {
      STATE.canalDetalhado = e.target.value;
      if (STATE.canalDetalhado !== 'ALL') {
        const ch = (DATA.canais || []).find(c => c.canal === STATE.canalDetalhado);
        if (ch) {
          if (ch.grupo === 'digital') {
            STATE.grupoCanal = 'digital';
            STATE.partMode = 'digital_empresa';
          } else if (ch.grupo === 'tele') {
            STATE.grupoCanal = 'tele';
            STATE.partMode = 'dt_empresa';
          } else if (ch.grupo === 'loja') {
            STATE.grupoCanal = 'loja';
            STATE.partMode = 'total_empresa';
          }
          if (grpCanalSel) grpCanalSel.value = STATE.grupoCanal;
          updatePartTabsUI();
        }
      }
      STATE.expandedCat.clear(); render();
    });
  }

  // Search
  if (sel('globalSearch')) {
    sel('globalSearch').addEventListener('input', e => {
      STATE.search = e.target.value.toLowerCase().trim(); render();
    });
  }

  // Sort
  if (sel('sortMode')) {
    sel('sortMode').addEventListener('change', e => { STATE.sort = e.target.value; render(); });
  }

  // Participation mode tabs
  const tabsContainer = sel('partModeTabs');
  if (tabsContainer) {
    tabsContainer.querySelectorAll('.part-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        tabsContainer.querySelectorAll('.part-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        STATE.partMode = tab.dataset.mode;
        STATE.expandedCat.clear();
        render();
      });
    });
  }

  // Section toggles
  document.querySelectorAll('.toggle-group input[data-section]').forEach(cb => {
    cb.addEventListener('change', () => {
      const sec = document.getElementById(cb.dataset.section);
      if (sec) sec.style.display = cb.checked ? '' : 'none';
    });
  });

  // Expand / Collapse all
  if (sel('btnExpandAll')) sel('btnExpandAll').addEventListener('click', () => {
    getFilteredGrupos().forEach(g => STATE.expandedCat.add(g.grupo));
    renderCategorias();
  });
  if (sel('btnCollapseAll')) sel('btnCollapseAll').addEventListener('click', () => { STATE.expandedCat.clear(); renderCategorias(); });

  // Column sorting on all sortable headers (Canais & Categorias)
  document.querySelectorAll('th.sortable').forEach(th => {
    th.addEventListener('click', () => {
      const sVal = th.dataset.sort;
      if (sel('sortMode')) sel('sortMode').value = sVal;
      STATE.sort = sVal;
      render();
    });
  });

  // Export & Print
  if (sel('btnExportCsv')) sel('btnExportCsv').addEventListener('click', exportCsv);
  if (sel('btnPrint')) sel('btnPrint').addEventListener('click', () => window.print());

  // Global click to close multi-select dropdowns
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.ms-container')) {
      document.querySelectorAll('.ms-container.open').forEach(c => c.classList.remove('open'));
    }
  });
}

function updatePartTabsUI() {
  const tabsContainer = sel('partModeTabs');
  if (tabsContainer) {
    tabsContainer.querySelectorAll('.part-tab').forEach(t => {
      t.classList.toggle('active', t.dataset.mode === STATE.partMode);
    });
  }
}

function sel(id) { return document.getElementById(id); }

/* ── Multi-Select Component Engine ─────────────────── */
function renderMultiSelect(containerId, optionsList, selectedSet, placeholderText, onChangeCallback) {
  const container = sel(containerId);
  if (!container) return;

  const currentSearch = container.querySelector('.ms-search')?.value.toLowerCase() || '';

  const selectedCount = selectedSet.size;
  let btnLabel = placeholderText;
  if (selectedCount > 0) {
    if (selectedCount === 1) btnLabel = Array.from(selectedSet)[0];
    else btnLabel = `${selectedCount} Selecionados`;
  }

  let html = `
    <button type="button" class="ms-btn">
      <span class="ms-btn-text">${esc(btnLabel)}</span>
      ${selectedCount > 1 ? `<span class="ms-badge">${selectedCount}</span>` : ''}
      <span class="ms-arrow">▼</span>
    </button>
    <div class="ms-dropdown">
      <input type="text" class="ms-search" placeholder="Pesquisar..." value="${esc(currentSearch)}">
      <div class="ms-actions">
        <button type="button" class="ms-action-btn btn-select-all">Selecionar Todos</button>
        <button type="button" class="ms-action-btn btn-clear-all">Limpar</button>
      </div>
      <div class="ms-list"></div>
    </div>
  `;

  container.innerHTML = html;

  const btn = container.querySelector('.ms-btn');
  const searchInput = container.querySelector('.ms-search');
  const btnSelectAll = container.querySelector('.btn-select-all');
  const btnClearAll = container.querySelector('.btn-clear-all');
  const listContainer = container.querySelector('.ms-list');

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    document.querySelectorAll('.ms-container.open').forEach(c => {
      if (c !== container) c.classList.remove('open');
    });
    container.classList.toggle('open');
    if (container.classList.contains('open')) searchInput.focus();
  });

  const renderItems = () => {
    const q = searchInput.value.toLowerCase().trim();
    const filteredOptions = optionsList.filter(opt => opt.toLowerCase().includes(q));

    if (filteredOptions.length === 0) {
      listContainer.innerHTML = '<div style="font-size:11px; color:#8b90a0; padding:4px;">Nenhum item encontrado</div>';
      return;
    }

    listContainer.innerHTML = filteredOptions.map(opt => {
      const isChecked = selectedSet.has(opt);
      return `
        <label class="ms-item">
          <input type="checkbox" value="${esc(opt)}" ${isChecked ? 'checked' : ''}>
          <span>${esc(opt)}</span>
        </label>
      `;
    }).join('');

    listContainer.querySelectorAll('input[type="checkbox"]').forEach(chk => {
      chk.addEventListener('change', (e) => {
        const val = e.target.value;
        if (e.target.checked) selectedSet.add(val);
        else selectedSet.delete(val);

        updateBtnState();
        if (onChangeCallback) onChangeCallback();
      });
    });
  };

  const updateBtnState = () => {
    const count = selectedSet.size;
    const txtEl = container.querySelector('.ms-btn-text');
    if (count === 0) {
      txtEl.textContent = placeholderText;
      const b = container.querySelector('.ms-badge');
      if (b) b.remove();
    } else if (count === 1) {
      txtEl.textContent = Array.from(selectedSet)[0];
      const b = container.querySelector('.ms-badge');
      if (b) b.remove();
    } else {
      txtEl.textContent = `${count} Selecionados`;
      let b = container.querySelector('.ms-badge');
      if (!b) {
        b = document.createElement('span');
        b.className = 'ms-badge';
        container.querySelector('.ms-btn').insertBefore(b, container.querySelector('.ms-arrow'));
      }
      b.textContent = count;
    }
  };

  searchInput.addEventListener('input', renderItems);

  btnSelectAll.addEventListener('click', () => {
    optionsList.forEach(opt => selectedSet.add(opt));
    renderItems();
    updateBtnState();
    if (onChangeCallback) onChangeCallback();
  });

  btnClearAll.addEventListener('click', () => {
    selectedSet.clear();
    renderItems();
    updateBtnState();
    if (onChangeCallback) onChangeCallback();
  });

  renderItems();
}

function initMultiSelects() {
  populateAllMultiSelects();
}

function populateAllMultiSelects() {
  const fh = DATA.filtroHierarquia || {};

  // Diretores
  const diretores = (fh.diretores || []).sort();
  renderMultiSelect('msDiretor', diretores, STATE.diretores, 'Todos os Diretores', () => {
    updateCascadingDistritais();
    STATE.expandedCat.clear(); render();
  });

  // Distritais com Cascata
  updateCascadingDistritais();

  // Coordenadores
  const coordenadores = (fh.coordenadores || []).sort();
  renderMultiSelect('msCoordenador', coordenadores, STATE.coordenadores, 'Todos os Coordenadores', () => {
    STATE.expandedCat.clear(); render();
  });

  // Grupos
  const grupos = (fh.grupos || []).sort();
  renderMultiSelect('msGrupo', grupos, STATE.grupos, 'Todos os Grupos', () => {
    updateCascadingSubgrupos();
    STATE.expandedCat.clear(); render();
  });

  updateCascadingSubgrupos();
}

function updateCascadingDistritais() {
  const hier = DATA.hierarquia || [];
  let availableDistritais = [];

  if (STATE.diretores.size > 0) {
    const filteredHier = hier.filter(h => h.diretor && STATE.diretores.has(h.diretor));
    availableDistritais = [...new Set(filteredHier.map(h => h.distrital).filter(Boolean))].sort();
  } else {
    availableDistritais = (DATA.filtroHierarquia.distritais || []).sort();
  }

  // Clean obsolete selected distritais
  Array.from(STATE.distritais).forEach(d => {
    if (!availableDistritais.includes(d)) STATE.distritais.delete(d);
  });

  renderMultiSelect('msDistrital', availableDistritais, STATE.distritais, 'Todas as Distritais', () => {
    updateCascadingGrupos();
    STATE.expandedCat.clear(); render();
  });
}

function updateCascadingGrupos() {
  const hier = DATA.hierarquia || [];
  let availableGrupos = [];

  let filteredHier = hier;
  if (STATE.diretores.size > 0) filteredHier = filteredHier.filter(h => h.diretor && STATE.diretores.has(h.diretor));
  if (STATE.distritais.size > 0) filteredHier = filteredHier.filter(h => h.distrital && STATE.distritais.has(h.distrital));

  if (STATE.diretores.size > 0 || STATE.distritais.size > 0) {
    availableGrupos = [...new Set(filteredHier.map(h => h.grupo).filter(Boolean))].sort();
  } else {
    availableGrupos = (DATA.filtroHierarquia.grupos || []).sort();
  }

  Array.from(STATE.grupos).forEach(g => {
    if (!availableGrupos.includes(g)) STATE.grupos.delete(g);
  });

  renderMultiSelect('msGrupo', availableGrupos, STATE.grupos, 'Todos os Grupos', () => {
    updateCascadingSubgrupos();
    STATE.expandedCat.clear(); render();
  });

  updateCascadingSubgrupos();
}

function updateCascadingSubgrupos() {
  const hier = DATA.hierarquia || [];
  let filteredHier = hier;

  if (STATE.diretores.size > 0) filteredHier = filteredHier.filter(h => h.diretor && STATE.diretores.has(h.diretor));
  if (STATE.distritais.size > 0) filteredHier = filteredHier.filter(h => h.distrital && STATE.distritais.has(h.distrital));
  if (STATE.grupos.size > 0) filteredHier = filteredHier.filter(h => STATE.grupos.has(h.grupo));

  let availableSubgrupos = [];
  if (STATE.grupos.size > 0 || STATE.diretores.size > 0 || STATE.distritais.size > 0) {
    availableSubgrupos = [...new Set(filteredHier.map(h => h.subgrupo).filter(Boolean))].sort();
  } else {
    availableSubgrupos = (DATA.filtroHierarquia.subgrupos || []).sort();
  }

  // Clean obsolete selected subgrupos
  Array.from(STATE.subgrupos).forEach(sg => {
    if (!availableSubgrupos.includes(sg)) STATE.subgrupos.delete(sg);
  });

  renderMultiSelect('msSubgrupo', availableSubgrupos, STATE.subgrupos, 'Todos os Subgrupos', () => {
    updateCascadingLinhas();
    STATE.expandedCat.clear(); render();
  });

  updateCascadingLinhas();
}

function updateCascadingLinhas() {
  const hier = DATA.hierarquia || [];
  let filteredHier = hier;

  if (STATE.diretores.size > 0) filteredHier = filteredHier.filter(h => h.diretor && STATE.diretores.has(h.diretor));
  if (STATE.distritais.size > 0) filteredHier = filteredHier.filter(h => h.distrital && STATE.distritais.has(h.distrital));
  if (STATE.grupos.size > 0) filteredHier = filteredHier.filter(h => STATE.grupos.has(h.grupo));
  if (STATE.subgrupos.size > 0) filteredHier = filteredHier.filter(h => STATE.subgrupos.has(h.subgrupo));

  let availableLinhas = [...new Set(filteredHier.map(h => h.linha).filter(Boolean))].sort();
  if (availableLinhas.length === 0 && STATE.grupos.size === 0 && STATE.subgrupos.size === 0) {
    availableLinhas = (DATA.filtroHierarquia.linhas || []).sort();
  }

  Array.from(STATE.linhas).forEach(l => {
    if (!availableLinhas.includes(l)) STATE.linhas.delete(l);
  });

  renderMultiSelect('msLinha', availableLinhas, STATE.linhas, 'Todas as Linhas', () => {
    updateCascadingLaboratorios();
    STATE.expandedCat.clear(); render();
  });

  updateCascadingLaboratorios();
}

function updateCascadingLaboratorios() {
  const hier = DATA.hierarquia || [];
  let filteredHier = hier;

  if (STATE.diretores.size > 0) filteredHier = filteredHier.filter(h => h.diretor && STATE.diretores.has(h.diretor));
  if (STATE.distritais.size > 0) filteredHier = filteredHier.filter(h => h.distrital && STATE.distritais.has(h.distrital));
  if (STATE.grupos.size > 0) filteredHier = filteredHier.filter(h => STATE.grupos.has(h.grupo));
  if (STATE.subgrupos.size > 0) filteredHier = filteredHier.filter(h => STATE.subgrupos.has(h.subgrupo));
  if (STATE.linhas.size > 0) filteredHier = filteredHier.filter(h => STATE.linhas.has(h.linha));

  let availableLabs = [...new Set(filteredHier.map(h => h.laboratorio).filter(Boolean))].sort();
  if (availableLabs.length === 0) {
    availableLabs = (DATA.filtroHierarquia.laboratorios || []).sort();
  }

  Array.from(STATE.laboratorios).forEach(lab => {
    if (!availableLabs.includes(lab)) STATE.laboratorios.delete(lab);
  });

  renderMultiSelect('msLaboratorio', availableLabs, STATE.laboratorios, 'Todos os Laboratórios', () => {
    STATE.expandedCat.clear(); render();
  });
}

function populateExclusionValues() {
  const excValSel = sel('filterExcluirValor');
  if (!excValSel) return;

  let list = [];
  if (STATE.excluirTipo === 'linha') list = DATA.filtroHierarquia.linhas || [];
  else if (STATE.excluirTipo === 'grupo') list = DATA.filtroHierarquia.grupos || [];
  else if (STATE.excluirTipo === 'subgrupo') list = DATA.filtroHierarquia.subgrupos || [];
  else if (STATE.excluirTipo === 'laboratorio') list = DATA.filtroHierarquia.laboratorios || [];
  else if (STATE.excluirTipo === 'canal') list = DATA.canais.map(c => c.canal);

  list = [...new Set(list)].sort();
  excValSel.innerHTML = '<option value="NONE">Selecione o item a EXCLUIR...</option>' +
    list.map(x => `<option value="${esc(x)}">${esc(x)}</option>`).join('');
}

/* ── Formatting ───────────────────────────────────── */
function fmtRS(val) {
  if (val == null || isNaN(val)) return '-';
  return val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0, maximumFractionDigits: 0 });
}
function fmtCompact(val) {
  if (val == null || isNaN(val)) return '-';
  const abs = Math.abs(val);
  if (abs >= 1e9) return 'R$ ' + (val / 1e9).toFixed(1).replace('.', ',') + ' Bi';
  if (abs >= 1e6) return 'R$ ' + (val / 1e6).toFixed(1).replace('.', ',') + ' Mi';
  if (abs >= 1e3) return 'R$ ' + Math.round(val / 1e3).toLocaleString('pt-BR') + ' Mil';
  return fmtRS(val);
}
function fmtPct(val) {
  if (val == null || isNaN(val)) return '-';
  return val.toFixed(2).replace('.', ',') + '%';
}
function badgePct(val) {
  if (val == null || isNaN(val)) return '<span class="badge neu">-</span>';
  if (Math.abs(val) < 0.001) return '<span class="badge neu">0,00%</span>';
  const cls = val > 0 ? 'pos' : 'neg';
  const arrow = val > 0 ? '▲' : '▼';
  const sign = val > 0 ? '+' : '-';
  return `<span class="badge ${cls}">${arrow} ${sign}${Math.abs(val).toFixed(2).replace('.', ',')}%</span>`;
}
function renderShareCell(pct) {
  if (pct == null || isNaN(pct)) return '-';
  const p = Math.max(0, Math.min(100, pct));
  return `
    <div class="share-bar-cell">
      <span>${fmtPct(pct)}</span>
      <div class="share-bar-bg"><div class="share-bar-fill" style="width: ${p.toFixed(1)}%;"></div></div>
    </div>
  `;
}

function badgePP(val) {
  if (val == null || isNaN(val)) return '<span class="apple-tag tag-neu">-</span>';
  if (Math.abs(val) < 0.001) return '<span class="apple-tag tag-neu">0,00 p.p.</span>';
  const cls = val > 0.001 ? 'tag-pos' : 'tag-neg';
  const arrow = val > 0.001 ? '▲' : '▼';
  const sign = val > 0 ? '+' : '-';
  return `<span class="apple-tag ${cls}">${arrow} ${sign}${Math.abs(val).toFixed(2).replace('.', ',')} p.p.</span>`;
}
function deltaRS(val) {
  if (val == null || isNaN(val)) return '-';
  if (Math.abs(val) < 0.01) return '<span class="delta-neu">R$ 0</span>';
  const cls = val > 0 ? 'delta-pos' : 'delta-neg';
  const sign = val > 0 ? '+' : '-';
  return `<span class="${cls}">${sign}${fmtRS(Math.abs(val))}</span>`;
}
function tagPct(val) {
  if (val == null || isNaN(val)) return '';
  if (Math.abs(val) < 0.001) return '<span class="apple-tag tag-neu">0,00%</span>';
  const cls = val > 0 ? 'tag-pos' : 'tag-neg';
  const arrow = val > 0 ? '▲' : '▼';
  const sign = val > 0 ? '+' : '-';
  return `<span class="apple-tag ${cls}">${arrow} ${sign}${Math.abs(val).toFixed(2).replace('.', ',')}%</span>`;
}
function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/* ── Filtered data helpers ────────────────────────── */
function applyHierarchyFilter(arr) {
  let items = arr;

  if (STATE.diretores.size > 0) items = items.filter(c => STATE.diretores.has(c.diretor));
  if (STATE.distritais.size > 0) items = items.filter(c => STATE.distritais.has(c.distrital));
  if (STATE.grupos.size > 0) items = items.filter(c => STATE.grupos.has(c.grupo));
  if (STATE.subgrupos.size > 0) items = items.filter(c => STATE.subgrupos.has(c.subgrupo));
  if (STATE.linhas.size > 0) items = items.filter(c => STATE.linhas.has(c.linha));
  if (STATE.laboratorios.size > 0) items = items.filter(c => STATE.laboratorios.has(c.laboratorio));

  if (STATE.excluirTipo !== 'NONE' && STATE.excluirValor !== 'NONE') {
    const prop = STATE.excluirTipo;
    items = items.filter(c => c[prop] !== STATE.excluirValor);
  }

  return items;
}

function getFilteredHier() {
  if ((STATE.canalDetalhado && STATE.canalDetalhado !== 'ALL') || (STATE.grupoCanal && STATE.grupoCanal !== 'ALL')) {
    let items = DATA.canaisHier || [];

    if (STATE.diretores.size > 0) items = items.filter(c => STATE.diretores.has(c.diretor));
    if (STATE.distritais.size > 0) items = items.filter(c => STATE.distritais.has(c.distrital));
    if (STATE.grupos.size > 0) items = items.filter(c => STATE.grupos.has(c.grupo));
    if (STATE.subgrupos.size > 0) items = items.filter(c => STATE.subgrupos.has(c.subgrupo));
    if (STATE.linhas.size > 0) items = items.filter(c => STATE.linhas.has(c.linha));
    if (STATE.laboratorios.size > 0) items = items.filter(c => STATE.laboratorios.has(c.laboratorio));

    if (STATE.excluirTipo !== 'NONE' && STATE.excluirValor !== 'NONE') {
      const prop = STATE.excluirTipo === 'grupo' ? 'grupo' :
                   STATE.excluirTipo === 'subgrupo' ? 'subgrupo' :
                   STATE.excluirTipo === 'linha' ? 'linha' :
                   STATE.excluirTipo === 'laboratorio' ? 'laboratorio' :
                   STATE.excluirTipo === 'canal' ? 'canal' : '';
      if (prop) items = items.filter(c => c[prop] !== STATE.excluirValor);
    }

    if (STATE.canalDetalhado && STATE.canalDetalhado !== 'ALL') {
      items = items.filter(c => c.canal === STATE.canalDetalhado);
    } else if (STATE.grupoCanal === 'digital') {
      items = items.filter(c => c.canal_grupo === 'digital');
    } else if (STATE.grupoCanal === 'tele') {
      items = items.filter(c => c.canal_grupo === 'tele');
    } else if (STATE.grupoCanal === 'digital_tele') {
      items = items.filter(c => c.canal_grupo === 'digital' || c.canal_grupo === 'tele');
    } else if (STATE.grupoCanal === 'loja') {
      items = items.filter(c => c.canal_grupo === 'loja');
    }

    const map = {};
    items.forEach(c => {
      const key = `${c.grupo}||${c.subgrupo}||${c.linha}`;
      if (!map[key]) {
        map[key] = {
          diretor: c.diretor, distrital: c.distrital,
          grupo: c.grupo, subgrupo: c.subgrupo, linha: c.linha,
          laboratorio: c.laboratorio || '',
          venda_jul_26: 0, venda_jun_26: 0, venda_jul_25: 0,
          venda_digital_jul_26: 0, venda_digital_jun_26: 0, venda_digital_jul_25: 0,
          venda_dt_jul_26: 0, venda_dt_jun_26: 0, venda_dt_jul_25: 0
        };
      }
      const v26 = c.v26 || 0;
      const v26_06 = c.v26_06 || 0;
      const v25 = c.v25 || 0;

      map[key].venda_jul_26 += v26;
      map[key].venda_jun_26 += v26_06;
      map[key].venda_jul_25 += v25;

      if (c.canal_grupo === 'digital') {
        map[key].venda_digital_jul_26 += v26;
        map[key].venda_digital_jun_26 += v26_06;
        map[key].venda_digital_jul_25 += v25;
        map[key].venda_dt_jul_26 += v26;
        map[key].venda_dt_jun_26 += v26_06;
        map[key].venda_dt_jul_25 += v25;
      } else if (c.canal_grupo === 'tele') {
        map[key].venda_dt_jul_26 += v26;
        map[key].venda_dt_jun_26 += v26_06;
        map[key].venda_dt_jul_25 += v25;
      }
    });

    return Object.values(map);
  }

  return applyHierarchyFilter(DATA.hierarquia);
}

/* ── Filtered Channels Helper ── */
function getFilteredCanaisList() {
  if (!DATA.canaisHier || !DATA.canaisHier.length) {
    let list = DATA.canais || [];
    if (STATE.excluirTipo === 'canal' && STATE.excluirValor !== 'NONE') {
      list = list.filter(c => c.canal !== STATE.excluirValor);
    }
    return list;
  }

  let items = DATA.canaisHier;

  if (STATE.diretores.size > 0) items = items.filter(c => STATE.diretores.has(c.diretor));
  if (STATE.distritais.size > 0) items = items.filter(c => STATE.distritais.has(c.distrital));
  if (STATE.grupos.size > 0) items = items.filter(c => STATE.grupos.has(c.grupo));
  if (STATE.subgrupos.size > 0) items = items.filter(c => STATE.subgrupos.has(c.subgrupo));
  if (STATE.linhas.size > 0) items = items.filter(c => STATE.linhas.has(c.linha));
  if (STATE.laboratorios.size > 0) items = items.filter(c => STATE.laboratorios.has(c.laboratorio));

  if (STATE.excluirTipo !== 'NONE' && STATE.excluirValor !== 'NONE') {
    const prop = STATE.excluirTipo === 'grupo' ? 'grupo' :
                 STATE.excluirTipo === 'subgrupo' ? 'subgrupo' :
                 STATE.excluirTipo === 'linha' ? 'linha' :
                 STATE.excluirTipo === 'laboratorio' ? 'laboratorio' :
                 STATE.excluirTipo === 'canal' ? 'canal' : '';
    if (prop) items = items.filter(c => c[prop] !== STATE.excluirValor);
  }

  if (STATE.canalDetalhado && STATE.canalDetalhado !== 'ALL') {
    items = items.filter(c => c.canal === STATE.canalDetalhado);
  } else if (STATE.grupoCanal === 'digital') {
    items = items.filter(c => c.canal_grupo === 'digital');
  } else if (STATE.grupoCanal === 'tele') {
    items = items.filter(c => c.canal_grupo === 'tele');
  } else if (STATE.grupoCanal === 'digital_tele') {
    items = items.filter(c => c.canal_grupo === 'digital' || c.canal_grupo === 'tele');
  } else if (STATE.grupoCanal === 'loja') {
    items = items.filter(c => c.canal_grupo === 'loja');
  }

  const map = {};
  items.forEach(c => {
    if (!map[c.canal]) {
      map[c.canal] = {
        canal: c.canal,
        grupo: c.canal_grupo,
        venda_jul_26: 0, venda_jun_26: 0, venda_jul_25: 0,
        d25: [], d26_06: [], d26_07: []
      };
    }
    map[c.canal].venda_jul_26 += (c.v26 || 0);
    map[c.canal].venda_jun_26 += (c.v26_06 || 0);
    map[c.canal].venda_jul_25 += (c.v25 || 0);

    if (c.d25) {
      if (!map[c.canal].d25.length) map[c.canal].d25 = [...c.d25];
      else c.d25.forEach((v, i) => map[c.canal].d25[i] = (map[c.canal].d25[i] || 0) + v);
    }
    if (c.d26_06) {
      if (!map[c.canal].d26_06.length) map[c.canal].d26_06 = [...c.d26_06];
      else c.d26_06.forEach((v, i) => map[c.canal].d26_06[i] = (map[c.canal].d26_06[i] || 0) + v);
    }
    if (c.d26_07) {
      if (!map[c.canal].d26_07.length) map[c.canal].d26_07 = [...c.d26_07];
      else c.d26_07.forEach((v, i) => map[c.canal].d26_07[i] = (map[c.canal].d26_07[i] || 0) + v);
    }
  });

  return Object.values(map);
}

function getFilteredGrupos() {
  const hier = getFilteredHier();
  const map = {};
  // useDays: ativo para qualquer mês quando há filtro de período != intervalo padrão
  const maxDiaAgo = (DATA.kpis?.periodo_info?.dias_fechados) || 19;
  const defaultEnd = STATE.mesReferencia === 'agosto' ? maxDiaAgo : 31;
  const useDays = (STATE.startDay !== 1 || STATE.endDay < defaultEnd);

  hier.forEach(c => {
    let v26 = c.venda_jul_26 || 0;
    let v26_06 = c.venda_jun_26 || 0;
    let v25 = c.venda_jul_25 || 0;

    let v_dig26 = c.venda_digital_jul_26 || 0;
    let v_dig26_06 = c.venda_digital_jun_26 || 0;
    let v_dig25 = c.venda_digital_jul_25 || 0;

    let v_dt26 = c.venda_dt_jul_26 || 0;
    let v_dt26_06 = c.venda_dt_jun_26 || 0;
    let v_dt25 = c.venda_dt_jul_25 || 0;

    if (useDays) {
      if (c.d26_07) v26 = sumDays(c.d26_07, STATE.startDay, STATE.endDay);
      if (c.d26_06) v26_06 = sumDays(c.d26_06, STATE.startDay, STATE.endDay);
      if (c.d25) v25 = sumDays(c.d25, STATE.startDay, STATE.endDay);

      if (c.dig_d26_07) v_dig26 = sumDays(c.dig_d26_07, STATE.startDay, STATE.endDay);
      if (c.dig_d26_06) v_dig26_06 = sumDays(c.dig_d26_06, STATE.startDay, STATE.endDay);
      if (c.dig_d25) v_dig25 = sumDays(c.dig_d25, STATE.startDay, STATE.endDay);

      if (c.dt_d26_07) v_dt26 = sumDays(c.dt_d26_07, STATE.startDay, STATE.endDay);
      if (c.dt_d26_06) v_dt26_06 = sumDays(c.dt_d26_06, STATE.startDay, STATE.endDay);
      if (c.dt_d25) v_dt25 = sumDays(c.dt_d25, STATE.startDay, STATE.endDay);
    }

    if (!map[c.grupo]) {
      map[c.grupo] = {
        grupo: c.grupo,
        venda_jul_26: 0, venda_jun_26: 0, venda_jul_25: 0,
        venda_digital_jul_26: 0, venda_digital_jun_26: 0, venda_digital_jul_25: 0,
        venda_dt_jul_26: 0, venda_dt_jun_26: 0, venda_dt_jul_25: 0
      };
    }

    map[c.grupo].venda_jul_26 += v26;
    map[c.grupo].venda_jun_26 += v26_06;
    map[c.grupo].venda_jul_25 += v25;

    map[c.grupo].venda_digital_jul_26 += v_dig26;
    map[c.grupo].venda_digital_jun_26 += v_dig26_06;
    map[c.grupo].venda_digital_jul_25 += v_dig25;

    map[c.grupo].venda_dt_jul_26 += v_dt26;
    map[c.grupo].venda_dt_jun_26 += v_dt26_06;
    map[c.grupo].venda_dt_jul_25 += v_dt25;
  });

  let grupos = Object.values(map).map(g => {
    g.mom_pct = g.venda_jun_26 > 0 ? ((g.venda_jul_26 / g.venda_jun_26) - 1) * 100 : 0;
    g.mom_rs = g.venda_jul_26 - g.venda_jun_26;
    g.yoy_pct = g.venda_jul_25 > 0 ? ((g.venda_jul_26 / g.venda_jul_25) - 1) * 100 : 0;
    g.yoy_rs = g.venda_jul_26 - g.venda_jul_25;
    return g;
  }).filter(g => g.venda_jul_26 !== 0 || g.venda_jun_26 !== 0 || g.venda_jul_25 !== 0);

  if (STATE.search) {
    grupos = grupos.filter(g => {
      if (g.grupo.toLowerCase().includes(STATE.search)) return true;
      return hier.some(h => h.grupo === g.grupo && h.linha && h.linha.toLowerCase().includes(STATE.search));
    });
  }

  // ORDENAÇÃO DINÂMICA NÍVEL 1 (GRUPOS)
  switch (STATE.sort) {
    case 'faturamento':
    case 'venda_jul_26':
    case 'jul26':
      grupos.sort((a, b) => {
        let va = a.venda_jul_26, vb = b.venda_jul_26;
        if (STATE.partMode === 'digital_empresa') { va = a.venda_digital_jul_26; vb = b.venda_digital_jul_26; }
        else if (STATE.partMode === 'dt_empresa') { va = a.venda_dt_jul_26; vb = b.venda_dt_jul_26; }
        return (vb || 0) - (va || 0);
      });
      break;
    case 'venda_jun_26':
    case 'jun26':
      grupos.sort((a, b) => (b.venda_jun_26 || 0) - (a.venda_jun_26 || 0));
      break;
    case 'venda_jul_25':
    case 'jul25':
      grupos.sort((a, b) => (b.venda_jul_25 || 0) - (a.venda_jul_25 || 0));
      break;
    case 'mom_pct':
      grupos.sort((a, b) => (b.mom_pct || 0) - (a.mom_pct || 0));
      break;
    case 'yoy_pct':
      grupos.sort((a, b) => (b.yoy_pct || 0) - (a.yoy_pct || 0));
      break;
    case 'mom_rs':
      grupos.sort((a, b) => (b.mom_rs || 0) - (a.mom_rs || 0));
      break;
    case 'yoy_rs':
      grupos.sort((a, b) => (b.yoy_rs || 0) - (a.yoy_rs || 0));
      break;
    case 'alpha':
      grupos.sort((a, b) => a.grupo.localeCompare(b.grupo));
      break;
  }

  return grupos;
}

/* ── Dynamic Table Headers ────────────────────────── */
function updateTableHeaders() {
  const isAgosto = (STATE.mesReferencia === 'agosto');
  const curLabel = isAgosto ? 'Ago/26' : 'Jul/26';
  const momLabel = isAgosto ? 'Jul/26' : 'Jun/26';
  const yoyLabel = isAgosto ? 'Ago/25' : 'Jul/25';

  // Canais table headers
  if (sel('thCanalCol1')) sel('thCanalCol1').textContent = curLabel;
  if (sel('thCanalCol2')) sel('thCanalCol2').textContent = `${momLabel} (MoM)`;
  if (sel('thCanalCol3')) sel('thCanalCol3').textContent = `${yoyLabel} (YoY)`;
  if (sel('thCanalPartCol1')) sel('thCanalPartCol1').textContent = `Share ${curLabel}`;
  if (sel('thCanalPartCol2')) sel('thCanalPartCol2').textContent = `Share ${momLabel}`;
  if (sel('thCanalPartCol3')) sel('thCanalPartCol3').textContent = `Share ${yoyLabel}`;

  // Categorias table headers
  if (sel('thCatCol1')) sel('thCatCol1').textContent = curLabel;
  if (sel('thCatCol2')) sel('thCatCol2').textContent = momLabel;
  if (sel('thCatCol3')) sel('thCatCol3').textContent = yoyLabel;
  if (sel('thPartJul26')) sel('thPartJul26').textContent = `Share ${curLabel}`;
  if (sel('thPartJun26')) sel('thPartJun26').textContent = `Share ${momLabel}`;
  if (sel('thPartJul25')) sel('thPartJul25').textContent = `Share ${yoyLabel}`;
}

/* ── Main render ──────────────────────────────────── */
function render() {
  updateTableHeaders();
  renderRefPeriodo();
  renderExecutiveKpis();
  renderCategorias();
  renderCanais();
  renderClientesTab();
  if (typeof updateCharts === 'function') updateCharts();
  // Update waterfall if its tab is currently active
  const wfTab = document.getElementById('tabWaterfall');
  if (wfTab && wfTab.classList.contains('active') && typeof triggerWaterfall === 'function') {
    triggerWaterfall();
  }
}

function renderRefPeriodo() {
  const el = sel('refPeriodoText') || sel('refPeriodo');
  if (!el) return;
  if (STATE.mesReferencia === 'agosto') {
    const pInfo = DATA.kpis?.periodo_info?.periodo_str || '01 a 18/08/2026';
    const maxDia = DATA.kpis?.periodo_info?.dias_fechados || 18;
    if (STATE.startDay === 1 && STATE.endDay >= maxDia) {
      el.textContent = `Agosto/2026 (${pInfo} D-1) • MoM vs Jul/26 • YoY vs Ago/25`;
    } else {
      const dS = String(STATE.startDay).padStart(2, '0');
      const dE = String(Math.min(STATE.endDay, maxDia)).padStart(2, '0');
      el.textContent = `Agosto/2026 (Dias ${dS} a ${dE}/08) • MoM vs Jul/26 • YoY vs Ago/25`;
    }
  } else {
    if (STATE.startDay === 1 && STATE.endDay === 31) {
      el.textContent = 'Julho/2026 (Fechado) • MoM vs Jun/26 • YoY vs Jul/25';
    } else {
      const dStart = String(STATE.startDay).padStart(2, '0');
      const dEnd = String(STATE.endDay).padStart(2, '0');
      el.textContent = `Julho/2026 (Dias ${dStart} a ${dEnd}/07) • Comparativo MTD`;
    }
  }
}

/* ── 6 KPI Cards Executivos 360° (Apple Style) ────────────── */
function renderExecutiveKpis() {
  const strip = sel('kpiStrip');
  if (!strip) return;

  const canais = getFilteredCanaisList();
  const maxDiaAgo = (DATA.kpis?.periodo_info?.dias_fechados) || 18;
  const defaultEnd = STATE.mesReferencia === 'agosto' ? maxDiaAgo : 31;
  const useDays = (STATE.startDay !== 1 || STATE.endDay < defaultEnd);

  const sumVal = (list, field) => list.reduce((s, c) => {
    let val = c[field] || 0;
    if (useDays) {
      const daysField = field === 'venda_jul_26' ? 'd26_07' :
                        field === 'venda_jun_26' ? 'd26_06' : 'd25';
      if (c[daysField] && c[daysField].length && c[daysField].some(x => x > 0)) {
        val = sumDays(c[daysField], STATE.startDay, STATE.endDay);
      }
    }
    return s + val;
  }, 0);

  const vJul26 = sumVal(canais, 'venda_jul_26');
  const vJun26 = sumVal(canais, 'venda_jun_26');
  const vJul25 = sumVal(canais, 'venda_jul_25');

  const digCanais = canais.filter(c => c.grupo === 'digital');
  const vDigJul26 = sumVal(digCanais, 'venda_jul_26');
  const vDigJun26 = sumVal(digCanais, 'venda_jun_26');
  const vDigJul25 = sumVal(digCanais, 'venda_jul_25');

  const dtCanais = canais.filter(c => c.grupo === 'digital' || c.grupo === 'tele');
  const vDtJul26 = sumVal(dtCanais, 'venda_jul_26');
  const vDtJun26 = sumVal(dtCanais, 'venda_jun_26');
  const vDtJul25 = sumVal(dtCanais, 'venda_jul_25');

  const lojaCanais = canais.filter(c => c.grupo === 'loja');
  const vLojaJul26 = sumVal(lojaCanais, 'venda_jul_26');
  const vLojaJun26 = sumVal(lojaCanais, 'venda_jun_26');
  const vLojaJul25 = sumVal(lojaCanais, 'venda_jul_25');

  const momPctTotal = vJun26 > 0 ? ((vJul26 / vJun26) - 1) * 100 : 0;
  const momRsTotal = vJul26 - vJun26;
  const yoyPctTotal = vJul25 > 0 ? ((vJul26 / vJul25) - 1) * 100 : 0;
  const yoyRsTotal = vJul26 - vJul25;

  const pctDig = vJul26 > 0 ? (vDigJul26 / vJul26 * 100) : 0;
  const digMom = vDigJun26 > 0 ? ((vDigJul26 / vDigJun26) - 1) * 100 : 0;
  const digYoy = vDigJul25 > 0 ? ((vDigJul26 / vDigJul25) - 1) * 100 : 0;

  const pctDt = vJul26 > 0 ? (vDtJul26 / vJul26 * 100) : 0;
  const dtMom = vDtJun26 > 0 ? ((vDtJul26 / vDtJun26) - 1) * 100 : 0;
  const dtYoy = vDtJul25 > 0 ? ((vDtJul26 / vDtJul25) - 1) * 100 : 0;

  const pctLoja = vJul26 > 0 ? (vLojaJul26 / vJul26 * 100) : 0;
  const lojaMom = vLojaJun26 > 0 ? ((vLojaJul26 / vLojaJun26) - 1) * 100 : 0;
  const lojaYoy = vLojaJul25 > 0 ? ((vLojaJul26 / vLojaJul25) - 1) * 100 : 0;

  const label1 = (STATE.mesReferencia === 'agosto')
      ? (() => {
          const pInfo = DATA.kpis?.periodo_info?.periodo_str || '01 a 18/08';
          const maxDia = DATA.kpis?.periodo_info?.dias_fechados || 18;
          if (STATE.startDay === 1 && STATE.endDay >= maxDia)
            return `FATURAMENTO LÍQUIDO (${pInfo})`;
          return `FATURAMENTO (DIAS ${STATE.startDay}-${Math.min(STATE.endDay, maxDia)}/08)`;
        })()
      : (STATE.startDay === 1 && STATE.endDay === 31) ? 'FATURAMENTO TOTAL (JUL/26)' : `FATURAMENTO (DIAS ${STATE.startDay}-${STATE.endDay}/07)`;

  strip.innerHTML = `
    <!-- Card 1: Faturamento Líquido (Consolidado) -->
    <div class="apple-kpi-card accent-blue">
      <div class="kpi-card-header">
        <span class="kpi-card-title">${esc(label1)}</span>
        <span class="apple-tag tag-neu">Total Rede</span>
      </div>
      <div class="kpi-value-main">${fmtCompact(vJul26)}</div>
      <div class="kpi-sub-value">${fmtRS(vJul26)}</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel" style="font-size: 11px; color: var(--text-secondary);">Faturamento líquido consolidado</span>
      </div>
    </div>

    <!-- Card 2: Crescimento MoM (Mês Anterior) -->
    <div class="apple-kpi-card ${momPctTotal >= 0 ? 'accent-green' : 'accent-red'}">
      <div class="kpi-card-header">
        <span class="kpi-card-title">CRESCIMENTO MoM</span>
        <span class="apple-tag ${momPctTotal >= 0 ? 'tag-pos' : 'tag-neg'}">vs Mês Ant.</span>
      </div>
      <div class="kpi-value-main" style="color: ${momPctTotal >= 0 ? 'var(--apple-green-text)' : 'var(--apple-red-text)'};">${fmtPct(momPctTotal)}</div>
      <div class="kpi-sub-value">${deltaRS(momRsTotal)} nominal</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">Base anterior: ${fmtCompact(vJun26)}</span>
      </div>
    </div>

    <!-- Card 3: Evolução YoY (Ano Anterior) -->
    <div class="apple-kpi-card ${yoyPctTotal >= 0 ? 'accent-green' : 'accent-red'}">
      <div class="kpi-card-header">
        <span class="kpi-card-title">EVOLUÇÃO YoY</span>
        <span class="apple-tag ${yoyPctTotal >= 0 ? 'tag-pos' : 'tag-neg'}">vs Ano Ant.</span>
      </div>
      <div class="kpi-value-main" style="color: ${yoyPctTotal >= 0 ? 'var(--apple-green-text)' : 'var(--apple-red-text)'};">${fmtPct(yoyPctTotal)}</div>
      <div class="kpi-sub-value">${deltaRS(yoyRsTotal)} nominal</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">Base anterior: ${fmtCompact(vJul25)}</span>
      </div>
    </div>

    <!-- Card 4: Share Digital -->
    <div class="apple-kpi-card accent-teal">
      <div class="kpi-card-header">
        <span class="kpi-card-title">SHARE DIGITAL</span>
        <span class="apple-tag tag-neu">App + Site + Parcerias</span>
      </div>
      <div class="kpi-value-main" style="color: var(--apple-teal);">${fmtPct(pctDig)}</div>
      <div class="kpi-sub-value">${fmtCompact(vDigJul26)}</div>
      <div class="kpi-footer-deltas">
        ${tagPct(digMom)} <span class="sublabel">MoM</span>
        ${tagPct(digYoy)} <span class="sublabel">YoY</span>
      </div>
    </div>

    <!-- Card 5: Share Digital + Tele -->
    <div class="apple-kpi-card accent-indigo">
      <div class="kpi-card-header">
        <span class="kpi-card-title">SHARE DIGITAL + TELE</span>
        <span class="apple-tag tag-neu">Vendas Remotas</span>
      </div>
      <div class="kpi-value-main" style="color: var(--apple-indigo);">${fmtPct(pctDt)}</div>
      <div class="kpi-sub-value">${fmtCompact(vDtJul26)}</div>
      <div class="kpi-footer-deltas">
        ${tagPct(dtMom)} <span class="sublabel">MoM</span>
        ${tagPct(dtYoy)} <span class="sublabel">YoY</span>
      </div>
    </div>

    <!-- Card 6: Share Loja Física -->
    <div class="apple-kpi-card accent-orange">
      <div class="kpi-card-header">
        <span class="kpi-card-title">SHARE LOJA FÍSICA</span>
        <span class="apple-tag tag-neu">Presencial</span>
      </div>
      <div class="kpi-value-main" style="color: var(--apple-orange);">${fmtPct(pctLoja)}</div>
      <div class="kpi-sub-value">${fmtCompact(vLojaJul26)}</div>
      <div class="kpi-footer-deltas">
        ${tagPct(lojaMom)} <span class="sublabel">MoM</span>
        ${tagPct(lojaYoy)} <span class="sublabel">YoY</span>
      </div>
    </div>
  `;
}

/* ── Canais table com Compilações Expansíveis & Ordenação Dinâmica Aplicada ─────── */
function renderCanais() {
  const tbody = sel('tbodyCanais');
  if (!tbody) return;

  const filteredCanaisList = getFilteredCanaisList();
  const maxDiaAgo = (DATA.kpis?.periodo_info?.dias_fechados) || 19;
  const defaultEnd = STATE.mesReferencia === 'agosto' ? maxDiaAgo : 31;
  const useDays = (STATE.startDay !== 1 || STATE.endDay < defaultEnd);

  const digitalChs = [];
  const teleChs = [];
  const dtChs = [];
  const lojaChs = [];

  let tot26 = 0, tot26_06 = 0, tot25 = 0;

  filteredCanaisList.forEach(c => {
    let v26 = c.venda_jul_26 || 0;
    let v26_06 = c.venda_jun_26 || 0;
    let v25 = c.venda_jul_25 || 0;

    if (useDays) {
      if (c.d26_07) v26 = sumDays(c.d26_07, STATE.startDay, STATE.endDay);
      if (c.d26_06) v26_06 = sumDays(c.d26_06, STATE.startDay, STATE.endDay);
      if (c.d25) v25 = sumDays(c.d25, STATE.startDay, STATE.endDay);
    }

    const m_rs = v26 - v26_06;
    const m_pct = v26_06 > 0 ? (m_rs / v26_06) * 100 : 0;
    const y_rs = v26 - v25;
    const y_pct = v25 > 0 ? (y_rs / v25) * 100 : 0;

    const item = {
      canal: c.canal,
      grupo: c.grupo,
      v26, v26_06, v25,
      mom_pct: m_pct, mom_rs: m_rs,
      yoy_pct: y_pct, yoy_rs: y_rs
    };

    if (c.grupo === 'digital') {
      digitalChs.push(item);
      dtChs.push(item);
    } else if (c.grupo === 'tele') {
      teleChs.push(item);
      dtChs.push(item);
    } else {
      lojaChs.push(item);
    }

    tot26 += v26;
    tot26_06 += v26_06;
    tot25 += v25;
  });

  const sortChannelItems = (items) => {
    switch (STATE.sort) {
      case 'faturamento':
      case 'venda_jul_26':
      case 'jul26':
        items.sort((a, b) => (b.v26 || 0) - (a.v26 || 0));
        break;
      case 'venda_jun_26':
      case 'jun26':
        items.sort((a, b) => (b.v26_06 || 0) - (a.v26_06 || 0));
        break;
      case 'venda_jul_25':
      case 'jul25':
        items.sort((a, b) => (b.v25 || 0) - (a.v25 || 0));
        break;
      case 'mom_pct':
        items.sort((a, b) => (b.mom_pct || 0) - (a.mom_pct || 0));
        break;
      case 'mom_rs':
        items.sort((a, b) => (b.mom_rs || 0) - (a.mom_rs || 0));
        break;
      case 'yoy_pct':
        items.sort((a, b) => (b.yoy_pct || 0) - (a.yoy_pct || 0));
        break;
      case 'yoy_rs':
        items.sort((a, b) => (b.yoy_rs || 0) - (a.yoy_rs || 0));
        break;
      case 'alpha':
        items.sort((a, b) => a.canal.localeCompare(b.canal));
        break;
    }
  };

  sortChannelItems(digitalChs);
  sortChannelItems(dtChs);
  sortChannelItems(lojaChs);

  const buildComp = (id, name, items) => {
    const v26 = items.reduce((s, x) => s + x.v26, 0);
    const v26_06 = items.reduce((s, x) => s + x.v26_06, 0);
    const v25 = items.reduce((s, x) => s + x.v25, 0);
    const m_rs = v26 - v26_06;
    const m_pct = v26_06 > 0 ? (m_rs / v26_06) * 100 : 0;
    const y_rs = v26 - v25;
    const y_pct = v25 > 0 ? (y_rs / v25) * 100 : 0;

    const sh26 = tot26 > 0 ? (v26 / tot26 * 100) : 0;
    const sh26_06 = tot26_06 > 0 ? (v26_06 / tot26_06 * 100) : 0;
    const sh25 = tot25 > 0 ? (v25 / tot25 * 100) : 0;
    const var_pp = sh26 - sh25;

    return { id, name, items, v26, v26_06, v25, mom_pct: m_pct, mom_rs: m_rs, yoy_pct: y_pct, yoy_rs: y_rs, sh26, sh26_06, sh25, var_pp };
  };

  const compDigital = buildComp('digital', 'Venda Digital', digitalChs);
  const compDT = buildComp('digital_tele', 'Venda Digital + Tele', dtChs);
  const compLoja = buildComp('loja', 'Venda Loja Física', lojaChs);

  const compilacoes = [compDigital, compDT, compLoja];

  let html = '';

  compilacoes.forEach(comp => {
    const isExp = STATE.expandedCh.has(comp.id);
    const toggleIcon = isExp ? '▼' : '▶';

    html += `
      <tr class="row-group" style="cursor:pointer;" onclick="toggleChGroup('${comp.id}')">
        <td class="col-grupo">
          <span class="toggle-icon">${toggleIcon}</span> <strong style="color: var(--apple-blue);">${esc(comp.name)}</strong>
        </td>
        <td class="num font-weight-600">${fmtRS(comp.v26)}</td>
        <td class="num">${fmtRS(comp.v26_06)}</td>
        <td class="num">${fmtRS(comp.v25)}</td>
        <td class="num">${badgePct(comp.mom_pct)}</td>
        <td class="num">${deltaRS(comp.mom_rs)}</td>
        <td class="num">${badgePct(comp.yoy_pct)}</td>
        <td class="num">${deltaRS(comp.yoy_rs)}</td>
        <td class="num">${renderShareCell(comp.sh26)}</td>
        <td class="num">${renderShareCell(comp.sh26_06)}</td>
        <td class="num">${renderShareCell(comp.sh25)}</td>
        <td class="num">${badgePP(comp.var_pp)}</td>
      </tr>
    `;

    if (isExp) {
      comp.items.forEach(c => {
        const c_sh26 = tot26 > 0 ? (c.v26 / tot26 * 100) : 0;
        const c_sh26_06 = tot26_06 > 0 ? (c.v26_06 / tot26_06 * 100) : 0;
        const c_sh25 = tot25 > 0 ? (c.v25 / tot25 * 100) : 0;
        const c_var_pp = c_sh26 - c_sh25;

        html += `
          <tr class="row-linha">
            <td class="col-linha" style="padding-left: 36px; color: var(--text-secondary);">└ ${esc(c.canal)}</td>
            <td class="num">${fmtRS(c.v26)}</td>
            <td class="num">${fmtRS(c.v26_06)}</td>
            <td class="num">${fmtRS(c.v25)}</td>
            <td class="num">${badgePct(c.mom_pct)}</td>
            <td class="num">${deltaRS(c.mom_rs)}</td>
            <td class="num">${badgePct(c.yoy_pct)}</td>
            <td class="num">${deltaRS(c.yoy_rs)}</td>
            <td class="num">${renderShareCell(c_sh26)}</td>
            <td class="num">${renderShareCell(c_sh26_06)}</td>
            <td class="num">${renderShareCell(c_sh25)}</td>
            <td class="num">${badgePP(c_var_pp)}</td>
          </tr>
        `;
      });
    }
  });

  const tot_mom_rs = tot26 - tot26_06;
  const tot_mom_pct = tot26_06 > 0 ? (tot_mom_rs / tot26_06) * 100 : 0;
  const tot_yoy_rs = tot26 - tot25;
  const tot_yoy_pct = tot25 > 0 ? (tot_yoy_rs / tot25) * 100 : 0;

  html += `
    <tr style="font-weight: 700; background: rgba(0, 113, 227, 0.06); border-top: 2px solid var(--border);">
      <td>EMPRESA TOTAL</td>
      <td class="num">${fmtRS(tot26)}</td>
      <td class="num">${fmtRS(tot26_06)}</td>
      <td class="num">${fmtRS(tot25)}</td>
      <td class="num">${badgePct(tot_mom_pct)}</td>
      <td class="num">${deltaRS(tot_mom_rs)}</td>
      <td class="num">${badgePct(tot_yoy_pct)}</td>
      <td class="num">${deltaRS(tot_yoy_rs)}</td>
      <td class="num">${renderShareCell(100)}</td>
      <td class="num">${renderShareCell(100)}</td>
      <td class="num">${renderShareCell(100)}</td>
      <td class="num">${badgePP(0)}</td>
    </tr>
  `;

  tbody.innerHTML = html;
}

function toggleChGroup(id) {
  if (STATE.expandedCh.has(id)) STATE.expandedCh.delete(id);
  else STATE.expandedCh.add(id);
  renderCanais();
}

/* ── Categorias table com Agregação Exata por Linha & Ordenação Dinâmica ─────────────── */
function renderCategorias() {
  const tbody = sel('tbodyCategorias');
  if (!tbody) return;

  const grupos = getFilteredGrupos();
  const hier = getFilteredHier();
  const maxDiaAgo2 = (DATA.kpis?.periodo_info?.dias_fechados) || 19;
  const defaultEnd2 = STATE.mesReferencia === 'agosto' ? maxDiaAgo2 : 31;
  const useDays = (STATE.startDay !== 1 || STATE.endDay < defaultEnd2);

  let totEmp26 = 0, totEmp26_06 = 0, totEmp25 = 0;
  totEmp26 = grupos.reduce((s, g) => s + (g.venda_jul_26 || 0), 0);
  totEmp26_06 = grupos.reduce((s, g) => s + (g.venda_jun_26 || 0), 0);
  totEmp25 = grupos.reduce((s, g) => s + (g.venda_jul_25 || 0), 0);

  let html = '';
  grupos.forEach(g => {
    let v26 = g.venda_jul_26, v26_06 = g.venda_jun_26, v25 = g.venda_jul_25;
    if (STATE.partMode === 'digital_empresa') {
      v26 = g.venda_digital_jul_26; v26_06 = g.venda_digital_jun_26; v25 = g.venda_digital_jul_25;
    } else if (STATE.partMode === 'dt_empresa') {
      v26 = g.venda_dt_jul_26; v26_06 = g.venda_dt_jun_26; v25 = g.venda_dt_jul_25;
    }

    const mom_rs = v26 - v26_06;
    const mom_pct = v26_06 > 0 ? (mom_rs / v26_06) * 100 : 0;
    const yoy_rs = v26 - v25;
    const yoy_pct = v25 > 0 ? (yoy_rs / v25) * 100 : 0;

    let sh26 = 0, sh26_06 = 0, sh25 = 0;
    if (STATE.partMode === 'digital_empresa') {
      // Penetração Digital da Categoria: Venda Digital do Grupo / Venda Total do Grupo
      sh26 = g.venda_jul_26 > 0 ? (g.venda_digital_jul_26 / g.venda_jul_26 * 100) : 0;
      sh26_06 = g.venda_jun_26 > 0 ? (g.venda_digital_jun_26 / g.venda_jun_26 * 100) : 0;
      sh25 = g.venda_jul_25 > 0 ? (g.venda_digital_jul_25 / g.venda_jul_25 * 100) : 0;
    } else if (STATE.partMode === 'dt_empresa') {
      // Penetração Digital+Tele da Categoria: Venda Digital+Tele do Grupo / Venda Total do Grupo
      sh26 = g.venda_jul_26 > 0 ? (g.venda_dt_jul_26 / g.venda_jul_26 * 100) : 0;
      sh26_06 = g.venda_jun_26 > 0 ? (g.venda_dt_jun_26 / g.venda_jun_26 * 100) : 0;
      sh25 = g.venda_jul_25 > 0 ? (g.venda_dt_jul_25 / g.venda_jul_25 * 100) : 0;
    } else {
      // Participação da Venda Total do Grupo no Total da Empresa
      sh26 = totEmp26 > 0 ? (g.venda_jul_26 / totEmp26 * 100) : 0;
      sh26_06 = totEmp26_06 > 0 ? (g.venda_jun_26 / totEmp26_06 * 100) : 0;
      sh25 = totEmp25 > 0 ? (g.venda_jul_25 / totEmp25 * 100) : 0;
    }
    const var_pp = sh26 - sh25;

    const isExp = STATE.expandedCat.has(g.grupo);
    const toggleIcon = isExp ? '▼' : '▶';

    html += `
      <tr class="row-group" data-grupo="${esc(g.grupo)}">
        <td class="col-grupo" style="cursor:pointer;" onclick="toggleCat('${esc(g.grupo)}')">
          <span class="toggle-icon">${toggleIcon}</span> <strong style="color: var(--text-primary);">${esc(g.grupo)}</strong>
        </td>
        <td class="num font-weight-600">${fmtRS(v26)}</td>
        <td class="num">${fmtRS(v26_06)}</td>
        <td class="num">${fmtRS(v25)}</td>
        <td class="num">${badgePct(mom_pct)}</td>
        <td class="num">${deltaRS(mom_rs)}</td>
        <td class="num">${badgePct(yoy_pct)}</td>
        <td class="num">${deltaRS(yoy_rs)}</td>
        <td class="num">${renderShareCell(sh26)}</td>
        <td class="num">${renderShareCell(sh26_06)}</td>
        <td class="num">${renderShareCell(sh25)}</td>
        <td class="num">${badgePP(var_pp)}</td>
      </tr>
    `;

    if (isExp) {
      // Group child items by LINHA to prevent duplicates and sum correctly
      const childRows = hier.filter(h => h.grupo === g.grupo);
      const linhaMap = {};

      childRows.forEach(h => {
        const key = h.linha || h.subgrupo || 'Outros';

        let tot_v26 = h.venda_jul_26 || 0;
        let tot_v26_06 = h.venda_jun_26 || 0;
        let tot_v25 = h.venda_jul_25 || 0;

        let dig_v26 = h.venda_digital_jul_26 || 0;
        let dig_v26_06 = h.venda_digital_jun_26 || 0;
        let dig_v25 = h.venda_digital_jul_25 || 0;

        let dt_v26 = h.venda_dt_jul_26 || 0;
        let dt_v26_06 = h.venda_dt_jun_26 || 0;
        let dt_v25 = h.venda_dt_jul_25 || 0;

        if (useDays) {
          if (h.d26_07) tot_v26 = sumDays(h.d26_07, STATE.startDay, STATE.endDay);
          if (h.d26_06) tot_v26_06 = sumDays(h.d26_06, STATE.startDay, STATE.endDay);
          if (h.d25) tot_v25 = sumDays(h.d25, STATE.startDay, STATE.endDay);

          if (h.dig_d26_07) dig_v26 = sumDays(h.dig_d26_07, STATE.startDay, STATE.endDay);
          if (h.dig_d26_06) dig_v26_06 = sumDays(h.dig_d26_06, STATE.startDay, STATE.endDay);
          if (h.dig_d25) dig_v25 = sumDays(h.dig_d25, STATE.startDay, STATE.endDay);

          if (h.dt_d26_07) dt_v26 = sumDays(h.dt_d26_07, STATE.startDay, STATE.endDay);
          if (h.dt_d26_06) dt_v26_06 = sumDays(h.dt_d26_06, STATE.startDay, STATE.endDay);
          if (h.dt_d25) dt_v25 = sumDays(h.dt_d25, STATE.startDay, STATE.endDay);
        }

        if (!linhaMap[key]) {
          linhaMap[key] = {
            linha: key,
            tot_v26: 0, tot_v26_06: 0, tot_v25: 0,
            dig_v26: 0, dig_v26_06: 0, dig_v25: 0,
            dt_v26: 0, dt_v26_06: 0, dt_v25: 0
          };
        }

        linhaMap[key].tot_v26 += tot_v26;
        linhaMap[key].tot_v26_06 += tot_v26_06;
        linhaMap[key].tot_v25 += tot_v25;

        linhaMap[key].dig_v26 += dig_v26;
        linhaMap[key].dig_v26_06 += dig_v26_06;
        linhaMap[key].dig_v25 += dig_v25;

        linhaMap[key].dt_v26 += dt_v26;
        linhaMap[key].dt_v26_06 += dt_v26_06;
        linhaMap[key].dt_v25 += dt_v25;
      });

      let subItems = Object.values(linhaMap).map(item => {
        let h_v26 = item.tot_v26, h_v26_06 = item.tot_v26_06, h_v25 = item.tot_v25;
        let h_sh26 = 0, h_sh26_06 = 0, h_sh25 = 0;

        if (STATE.partMode === 'digital_empresa') {
          h_v26 = item.dig_v26; h_v26_06 = item.dig_v26_06; h_v25 = item.dig_v25;
          h_sh26 = item.tot_v26 > 0 ? (item.dig_v26 / item.tot_v26 * 100) : 0;
          h_sh26_06 = item.tot_v26_06 > 0 ? (item.dig_v26_06 / item.tot_v26_06 * 100) : 0;
          h_sh25 = item.tot_v25 > 0 ? (item.dig_v25 / item.tot_v25 * 100) : 0;
        } else if (STATE.partMode === 'dt_empresa') {
          h_v26 = item.dt_v26; h_v26_06 = item.dt_v26_06; h_v25 = item.dt_v25;
          h_sh26 = item.tot_v26 > 0 ? (item.dt_v26 / item.tot_v26 * 100) : 0;
          h_sh26_06 = item.tot_v26_06 > 0 ? (item.dt_v26_06 / item.tot_v26_06 * 100) : 0;
          h_sh25 = item.tot_v25 > 0 ? (item.dt_v25 / item.tot_v25 * 100) : 0;
        } else {
          h_sh26 = totEmp26 > 0 ? (item.tot_v26 / totEmp26 * 100) : 0;
          h_sh26_06 = totEmp26_06 > 0 ? (item.tot_v26_06 / totEmp26_06 * 100) : 0;
          h_sh25 = totEmp25 > 0 ? (item.tot_v25 / totEmp25 * 100) : 0;
        }

        const h_mom_rs = h_v26 - h_v26_06;
        const h_mom_pct = h_v26_06 > 0 ? (h_mom_rs / h_v26_06) * 100 : 0;
        const h_yoy_rs = h_v26 - h_v25;
        const h_yoy_pct = h_v25 > 0 ? (h_yoy_rs / h_v25) * 100 : 0;
        const h_var_pp = h_sh26 - h_sh25;

        return {
          linha: item.linha,
          h_v26, h_v26_06, h_v25,
          h_mom_rs, h_mom_pct,
          h_yoy_rs, h_yoy_pct,
          h_sh26, h_sh26_06, h_sh25, h_var_pp
        };
      });

      // RANQUEAMENTO / ORDENAÇÃO DINÂMICA DO NÍVEL 2 (LINHAS)
      switch (STATE.sort) {
        case 'faturamento':
        case 'venda_jul_26':
        case 'jul26':
          subItems.sort((a, b) => (b.h_v26 || 0) - (a.h_v26 || 0));
          break;
        case 'venda_jun_26':
        case 'jun26':
          subItems.sort((a, b) => (b.h_v26_06 || 0) - (a.h_v26_06 || 0));
          break;
        case 'venda_jul_25':
        case 'jul25':
          subItems.sort((a, b) => (b.h_v25 || 0) - (a.h_v25 || 0));
          break;
        case 'mom_pct':
          subItems.sort((a, b) => (b.h_mom_pct || 0) - (a.h_mom_pct || 0));
          break;
        case 'yoy_pct':
          subItems.sort((a, b) => (b.h_yoy_pct || 0) - (a.h_yoy_pct || 0));
          break;
        case 'mom_rs':
          subItems.sort((a, b) => (b.h_mom_rs || 0) - (a.h_mom_rs || 0));
          break;
        case 'yoy_rs':
          subItems.sort((a, b) => (b.h_yoy_rs || 0) - (a.h_yoy_rs || 0));
          break;
        case 'alpha':
          subItems.sort((a, b) => a.linha.localeCompare(b.linha));
          break;
      }

      subItems.forEach(h => {
        html += `
          <tr class="row-linha">
            <td class="col-linha" style="padding-left: 36px; color: var(--text-secondary);">└ ${esc(h.linha)}</td>
            <td class="num">${fmtRS(h.h_v26)}</td>
            <td class="num">${fmtRS(h.h_v26_06)}</td>
            <td class="num">${fmtRS(h.h_v25)}</td>
            <td class="num">${badgePct(h.h_mom_pct)}</td>
            <td class="num">${deltaRS(h.h_mom_rs)}</td>
            <td class="num">${badgePct(h.h_yoy_pct)}</td>
            <td class="num">${deltaRS(h.h_yoy_rs)}</td>
            <td class="num">${renderShareCell(h.h_sh26)}</td>
            <td class="num">${renderShareCell(h.h_sh26_06)}</td>
            <td class="num">${renderShareCell(h.h_sh25)}</td>
            <td class="num">${badgePP(h.h_var_pp)}</td>
          </tr>
        `;
      });
    }
  });

  tbody.innerHTML = html;
}

function toggleCat(grupo) {
  if (STATE.expandedCat.has(grupo)) STATE.expandedCat.delete(grupo);
  else STATE.expandedCat.add(grupo);
  renderCategorias();
}

function exportCsv() {
  const grupos = getFilteredGrupos();
  let csv = 'Grupo;Venda_Jul_26;Venda_Jun_26;MoM_Pct;MoM_RS;Venda_Jul_25;YoY_Pct;YoY_RS\n';
  grupos.forEach(g => {
    csv += `"${g.grupo}";${g.venda_jul_26};${g.venda_jun_26};${g.mom_pct};${g.mom_rs};${g.venda_jul_25};${g.yoy_pct};${g.yoy_rs}\n`;
  });
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'acompanhamento_categorias.csv'; a.click();
}

function fmtInt(val) {
  if (val == null || isNaN(val)) return '-';
  return Math.round(val).toLocaleString('pt-BR');
}

/* ── Renderização da Aba Clientes Únicos & Cupons (360°) ─── */
function renderClientesTab() {
  const strip = sel('kpiStripClientes');
  const tbodyCanais = sel('tbodyClientesCanais');
  const tbodyGrupos = sel('tbodyClientesGrupos');
  if (!strip || !tbodyCanais || !tbodyGrupos) return;

  const cliData = DATA.clientes;
  if (!cliData || !cliData.totais) {
    strip.innerHTML = '<div class="apple-kpi-card accent-blue"><div class="kpi-value-main" style="font-size:16px;">Dados de clientes disponíveis apenas na base de Agosto</div></div>';
    tbodyCanais.innerHTML = '<tr><td colspan="10" style="text-align:center; padding:20px; color:var(--text-tertiary);">Dados de clientes disponíveis na base de Agosto (D-1 Qlik Sense).</td></tr>';
    tbodyGrupos.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:20px; color:var(--text-tertiary);">Dados de clientes disponíveis na base de Agosto (D-1 Qlik Sense).</td></tr>';
    return;
  }

  const tot = cliData.totais;
  const canais = cliData.canais || [];
  const grupos = cliData.grupos || [];

  // Calcular clientes digitais somando canais digitais
  const digChs = canais.filter(c => ['APP', 'SITE', 'iFood', 'e_Commerce', 'APP Tele Entrega', 'SITE Tele Entrega', 'Super Fácil', 'Mercado Livre', 'Rappi'].some(n => c.canal.toLowerCase().includes(n.toLowerCase())));
  const totCliDig = digChs.reduce((s, c) => s + (c.cli_26 || 0), 0);
  const pctCliDig = tot.cli_26 > 0 ? (totCliDig / tot.cli_26 * 100) : 0;

  // 1. Renderizar 6 KPI Cards Apple de Clientes
  strip.innerHTML = `
    <!-- Card 1: Total Clientes -->
    <div class="apple-kpi-card accent-blue">
      <div class="kpi-card-header">
        <span class="kpi-card-title">CLIENTES ÚNICOS ATIVOS</span>
        <span class="apple-tag tag-neu">Total D-1</span>
      </div>
      <div class="kpi-value-main">${fmtInt(tot.cli_26)}</div>
      <div class="kpi-sub-value">${fmtCompact(tot.cli_26).replace('R$ ', '')} compradores no período</div>
      <div class="kpi-footer-deltas">
        ${tagPct(tot.cli_mom_pct)} <span class="sublabel">MoM</span>
        ${tagPct(tot.cli_yoy_pct)} <span class="sublabel">YoY</span>
      </div>
    </div>

    <!-- Card 2: Total Cupons -->
    <div class="apple-kpi-card accent-indigo">
      <div class="kpi-card-header">
        <span class="kpi-card-title">CUPONS / TRANSAÇÕES</span>
        <span class="apple-tag tag-neu">Volume</span>
      </div>
      <div class="kpi-value-main" style="color: var(--apple-indigo);">${fmtInt(tot.cup_26)}</div>
      <div class="kpi-sub-value">${fmtCompact(tot.cup_26).replace('R$ ', '')} transações emitidas</div>
      <div class="kpi-footer-deltas">
        ${tagPct(tot.cup_mom_pct)} <span class="sublabel">MoM</span>
        ${tagPct(tot.cup_yoy_pct)} <span class="sublabel">YoY</span>
      </div>
    </div>

    <!-- Card 3: Ticket Médio -->
    <div class="apple-kpi-card accent-green">
      <div class="kpi-card-header">
        <span class="kpi-card-title">TICKET MÉDIO</span>
        <span class="apple-tag tag-pos">R$ / Cupom</span>
      </div>
      <div class="kpi-value-main" style="color: var(--apple-green-text);">${fmtRS(tot.ticket_medio)}</div>
      <div class="kpi-sub-value">Faturamento / Cupons</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">Frequência: ${tot.freq_media.toFixed(2).replace('.', ',')} compras/cli</span>
      </div>
    </div>

    <!-- Card 4: Gasto Médio por Cliente -->
    <div class="apple-kpi-card accent-orange">
      <div class="kpi-card-header">
        <span class="kpi-card-title">GASTO MÉDIO / CLIENTE</span>
        <span class="apple-tag tag-neu">R$ / Cliente</span>
      </div>
      <div class="kpi-value-main" style="color: var(--apple-orange);">${fmtRS(tot.gasto_medio)}</div>
      <div class="kpi-sub-value">Faturamento / Clientes Ativos</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">No período de 01 a 18/08</span>
      </div>
    </div>

    <!-- Card 5: Frequência de Compra -->
    <div class="apple-kpi-card accent-purple">
      <div class="kpi-card-header">
        <span class="kpi-card-title">FREQUÊNCIA DE COMPRA</span>
        <span class="apple-tag tag-neu">Cupons/Cli</span>
      </div>
      <div class="kpi-value-main" style="color: var(--apple-purple);">${tot.freq_media.toFixed(2).replace('.', ',')}x</div>
      <div class="kpi-sub-value">Média de idas à farmácia</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">Taxa de recorrência ativa</span>
      </div>
    </div>

    <!-- Card 6: Clientes Digitais -->
    <div class="apple-kpi-card accent-teal">
      <div class="kpi-card-header">
        <span class="kpi-card-title">CLIENTES DIGITAIS</span>
        <span class="apple-tag tag-neu">App + Site + Parcerias</span>
      </div>
      <div class="kpi-value-main" style="color: var(--apple-teal);">${fmtInt(totCliDig)}</div>
      <div class="kpi-sub-value">${fmtPct(pctCliDig)} de penetração nos clientes</div>
      <div class="kpi-footer-deltas">
        <span class="sublabel">Compradores digitais únicos</span>
      </div>
    </div>
  `;

  // 2. Renderizar Tabela de Canais por Clientes
  const sortedCanais = [...canais].sort((a, b) => (b.cli_26 || 0) - (a.cli_26 || 0));
  let canaisHtml = '';
  sortedCanais.forEach(c => {
    canaisHtml += `
      <tr class="row-linha">
        <td style="font-weight: 600; color: var(--text-primary);">${esc(c.canal)}</td>
        <td class="num font-weight-600">${fmtInt(c.cli_26)}</td>
        <td class="num">${fmtInt(c.cli_26_06)}</td>
        <td class="num">${fmtInt(c.cli_25)}</td>
        <td class="num">${badgePct(c.cli_mom_pct)}</td>
        <td class="num">${badgePct(c.cli_yoy_pct)}</td>
        <td class="num">${fmtInt(c.cup_26)}</td>
        <td class="num">${fmtRS(c.ticket_medio)}</td>
        <td class="num">${fmtRS(c.gasto_medio)}</td>
        <td class="num">${renderShareCell(c.penetr_base)}</td>
      </tr>
    `;
  });

  canaisHtml += `
    <tr style="font-weight: 700; background: rgba(0, 113, 227, 0.06); border-top: 2px solid var(--border);">
      <td>TOTAL GERAL DA REDE</td>
      <td class="num font-weight-600">${fmtInt(tot.cli_26)}</td>
      <td class="num">${fmtInt(tot.cli_26_06)}</td>
      <td class="num">${fmtInt(tot.cli_25)}</td>
      <td class="num">${badgePct(tot.cli_mom_pct)}</td>
      <td class="num">${badgePct(tot.cli_yoy_pct)}</td>
      <td class="num">${fmtInt(tot.cup_26)}</td>
      <td class="num">${fmtRS(tot.ticket_medio)}</td>
      <td class="num">${fmtRS(tot.gasto_medio)}</td>
      <td class="num">${renderShareCell(100)}</td>
    </tr>
  `;
  tbodyCanais.innerHTML = canaisHtml;

  // 3. Renderizar Tabela de Categorias por Clientes
  const sortedGrupos = [...grupos].sort((a, b) => (b.cli_26 || 0) - (a.cli_26 || 0));
  let gruposHtml = '';
  sortedGrupos.forEach(g => {
    gruposHtml += `
      <tr class="row-linha">
        <td style="font-weight: 600; color: var(--text-primary);">${esc(g.grupo)}</td>
        <td class="num font-weight-600">${fmtInt(g.cli_26)}</td>
        <td class="num">${fmtInt(g.cli_26_06)}</td>
        <td class="num">${fmtInt(g.cli_25)}</td>
        <td class="num">${badgePct(g.cli_yoy_pct)}</td>
        <td class="num">${fmtRS(g.venda_26)}</td>
        <td class="num">${fmtRS(g.gasto_medio)}</td>
        <td class="num">${renderShareCell(g.penetr_base)}</td>
      </tr>
    `;
  });
  tbodyGrupos.innerHTML = gruposHtml;
}
