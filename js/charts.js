/* charts.js — Gráficos Apple HIG para Mix de Canais & Penetração Digital */

let chartTrend = null;
let chartMix = null;

function updateCharts() {
  const trendCtx = document.getElementById('chartDigitalTrend');
  const mixCtx = document.getElementById('chartChannelMix');
  if (!trendCtx || !mixCtx) return;

  const canaisList = (typeof getFilteredCanaisList === 'function') ? getFilteredCanaisList() : (DATA.canais || []);
  const maxDiaAgo = (DATA.kpis?.periodo_info?.dias_fechados) || 18;
  const defaultEnd = (typeof STATE !== 'undefined' && STATE.mesReferencia === 'agosto') ? maxDiaAgo : 31;
  const useDays = (typeof STATE !== 'undefined') && (STATE.startDay !== 1 || STATE.endDay < defaultEnd);

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

  const isAgosto = (typeof STATE !== 'undefined' && STATE.mesReferencia === 'agosto');
  const labelsHist = isAgosto ? ['Ago/25 (YoY)', 'Jul/26 (MoM)', 'Ago/26 (D-1)'] : ['Jul/25 (YoY)', 'Jun/26 (MoM)', 'Jul/26 (Fechado)'];

  // Chart 1: Penetração Digital sobre Empresa (%) — Apple Line Style
  if (chartTrend) chartTrend.destroy();
  chartTrend = new Chart(trendCtx, {
    type: 'line',
    data: {
      labels: labelsHist,
      datasets: [
        {
          label: '% Digital / Empresa',
          data: [pctDig25, pctDig26_06, pctDig26_07],
          borderColor: '#0071E3',
          backgroundColor: 'rgba(0, 113, 227, 0.08)',
          fill: true,
          tension: 0.35,
          borderWidth: 3,
          pointRadius: 5,
          pointBackgroundColor: '#0071E3',
          pointHoverRadius: 7
        },
        {
          label: '% Digital + Tele / Empresa',
          data: [pctDt25, pctDt26_06, pctDt26_07],
          borderColor: '#34C759',
          backgroundColor: 'transparent',
          borderDash: [5, 5],
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: 4,
          pointBackgroundColor: '#34C759',
          pointHoverRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            font: { family: '-apple-system, Inter', size: 12, weight: '600' },
            usePointStyle: true,
            boxWidth: 8
          }
        },
        tooltip: {
          backgroundColor: 'rgba(29, 29, 31, 0.92)',
          titleFont: { family: '-apple-system, Inter', size: 12, weight: '700' },
          bodyFont: { family: '-apple-system, Inter', size: 12 },
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: ${ctx.raw.toFixed(2).replace('.', ',')}%`
          }
        }
      },
      scales: {
        y: {
          grid: { color: 'rgba(0, 0, 0, 0.04)' },
          ticks: {
            font: { family: '-apple-system, Inter', size: 11 },
            callback: v => v.toFixed(1) + '%'
          }
        },
        x: {
          grid: { display: false },
          ticks: { font: { family: '-apple-system, Inter', size: 11, weight: '600' } }
        }
      }
    }
  });

  // Chart 2: Mix de Canais — Apple Donut Style
  const pctLoja = tot26_07 > 0 ? (loja26_07 / tot26_07 * 100) : 0;
  const pctTele = tot26_07 > 0 ? (tele26_07 / tot26_07 * 100) : 0;
  const pctDig = tot26_07 > 0 ? (dig26_07 / tot26_07 * 100) : 0;

  if (chartMix) chartMix.destroy();
  chartMix = new Chart(mixCtx, {
    type: 'doughnut',
    data: {
      labels: ['Loja Física (Varejo)', 'Canais Digitais', 'Televendas & Tele-entrega'],
      datasets: [
        {
          data: [pctLoja, pctDig, pctTele],
          backgroundColor: ['#5856D6', '#0071E3', '#30B0C7'],
          borderWidth: 2,
          borderColor: '#FFFFFF',
          hoverOffset: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            font: { family: '-apple-system, Inter', size: 11, weight: '600' },
            usePointStyle: true,
            padding: 14
          }
        },
        tooltip: {
          backgroundColor: 'rgba(29, 29, 31, 0.92)',
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.raw.toFixed(2).replace('.', ',')}%`
          }
        }
      }
    }
  });
}
