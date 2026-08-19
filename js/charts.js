/* charts.js — Gráficos de Evolução da Penetração Digital & Mix de Canais */

let chartTrend = null;
let chartMix = null;

function updateCharts() {
  const trendCtx = document.getElementById('chartDigitalTrend');
  const mixCtx = document.getElementById('chartChannelMix');
  if (!trendCtx || !mixCtx) return;

  const canaisList = (typeof getFilteredCanaisList === 'function') ? getFilteredCanaisList() : (DATA.canais || []);
  const useDays = (typeof STATE !== 'undefined' && STATE.mesReferencia === 'julho') && (STATE.startDay !== 1 || STATE.endDay !== 31);

  let dig25 = 0, dig26_06 = 0, dig26_07 = 0;
  let dt25 = 0, dt26_06 = 0, dt26_07 = 0;
  let tot25 = 0, tot26_06 = 0, tot26_07 = 0;
  let loja26_07 = 0, tele26_07 = 0;

  canaisList.forEach(c => {
    let v26 = c.venda_jul_26 || 0;
    let v26_06 = c.venda_jun_26 || 0;
    let v25 = c.venda_jul_25 || 0;

    if (useDays) {
      if (c.d26_07) v26 = sumDays(c.d26_07, STATE.startDay, STATE.endDay);
      if (c.d26_06) v26_06 = sumDays(c.d26_06, STATE.startDay, STATE.endDay);
      if (c.d25) v25 = sumDays(c.d25, STATE.startDay, STATE.endDay);
    }

    tot26_07 += v26;
    tot26_06 += v26_06;
    tot25 += v25;

    if (c.grupo === 'digital') {
      dig26_07 += v26;
      dig26_06 += v26_06;
      dig25 += v25;
      dt26_07 += v26;
      dt26_06 += v26_06;
      dt25 += v25;
    } else if (c.grupo === 'tele') {
      tele26_07 += v26;
      dt26_07 += v26;
      dt26_06 += v26_06;
      dt25 += v25;
    } else {
      loja26_07 += v26;
    }
  });

  const pctDig25 = tot25 > 0 ? (dig25 / tot25 * 100) : 0;
  const pctDig26_06 = tot26_06 > 0 ? (dig26_06 / tot26_06 * 100) : 0;
  const pctDig26_07 = tot26_07 > 0 ? (dig26_07 / tot26_07 * 100) : 0;

  const pctDt25 = tot25 > 0 ? (dt25 / tot25 * 100) : 0;
  const pctDt26_06 = tot26_06 > 0 ? (dt26_06 / tot26_06 * 100) : 0;
  const pctDt26_07 = tot26_07 > 0 ? (dt26_07 / tot26_07 * 100) : 0;

  // Chart 1: Penetração Digital sobre Empresa (%)
  if (chartTrend) chartTrend.destroy();
  chartTrend = new Chart(trendCtx, {
    type: 'line',
    data: {
      labels: (typeof STATE !== 'undefined' && STATE.mesReferencia === 'agosto') ? ['Ago/25', 'Jul/26', 'Ago/26'] : ['Jul/25', 'Jun/26', 'Jul/26'],
      datasets: [
        {
          label: '% Digital / Empresa',
          data: [pctDig25, pctDig26_06, pctDig26_07],
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99,102,241,0.1)',
          fill: true,
          tension: 0.3,
          borderWidth: 3,
          pointRadius: 5,
          pointBackgroundColor: '#6366f1'
        },
        {
          label: '% Digital+Tele / Empresa',
          data: [pctDt25, pctDt26_06, pctDt26_07],
          borderColor: '#10b981',
          backgroundColor: 'transparent',
          borderDash: [5, 5],
          tension: 0.3,
          borderWidth: 2.5,
          pointRadius: 4,
          pointBackgroundColor: '#10b981'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { font: { family: 'Inter', size: 12, weight: '600' } } },
        tooltip: {
          callbacks: {
            label: ctx => ctx.dataset.label + ': ' + ctx.raw.toFixed(2).replace('.', ',') + '%'
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: v => v.toFixed(1).replace('.', ',') + '%',
            font: { family: 'Inter', size: 11 }
          }
        },
        x: {
          ticks: { font: { family: 'Inter', size: 11 } }
        }
      }
    }
  });

  // Chart 2: Mix de Canais — Mês Atual
  const pDig = tot26_07 > 0 ? (dig26_07 / tot26_07 * 100).toFixed(2).replace('.', ',') : '0';
  const pTele = tot26_07 > 0 ? (tele26_07 / tot26_07 * 100).toFixed(2).replace('.', ',') : '0';
  const pLoja = tot26_07 > 0 ? (loja26_07 / tot26_07 * 100).toFixed(2).replace('.', ',') : '0';

  if (chartMix) chartMix.destroy();
  chartMix = new Chart(mixCtx, {
    type: 'doughnut',
    data: {
      labels: [`Digital (${pDig}%)`, `Televendas (${pTele}%)`, `Loja Física (${pLoja}%)`],
      datasets: [{
        data: [dig26_07, tele26_07, loja26_07],
        backgroundColor: ['#6366f1', '#10b981', '#cbd5e1']
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { font: { family: 'Inter', size: 12, weight: '600' } } },
        tooltip: {
          callbacks: {
            label: ctx => ctx.label + ': R$ ' + Math.round(ctx.raw).toLocaleString('pt-BR')
          }
        }
      }
    }
  });
}
