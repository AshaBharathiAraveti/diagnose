/**
 * FreshSense — Chart.js Analytics
 * Robust chart rendering with proper sizing and error handling.
 */

/* ── Default theme ──────────────────────────────────────── */
Chart.defaults.color        = '#94a3b8';
Chart.defaults.borderColor  = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family  = "'Inter', system-ui, sans-serif";
Chart.defaults.font.size    = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding       = 14;
Chart.defaults.plugins.tooltip.padding             = 10;
Chart.defaults.plugins.tooltip.backgroundColor     = 'rgba(17,24,39,0.95)';
Chart.defaults.plugins.tooltip.borderWidth         = 1;
Chart.defaults.plugins.tooltip.borderColor         = 'rgba(255,255,255,0.1)';
Chart.defaults.plugins.tooltip.titleColor          = '#f1f5f9';
Chart.defaults.plugins.tooltip.bodyColor           = '#94a3b8';

const STATUS_COLORS = {
  fresh:    '#10b981',
  good:     '#34d399',
  moderate: '#f59e0b',
  spoiling: '#f97316',
  spoiled:  '#ef4444',
  unknown:  '#475569',
};

const CHART_PALETTE = [
  '#00d4aa', '#7c3aed', '#0ea5e9', '#f59e0b', '#ef4444',
  '#34d399', '#f97316', '#6366f1', '#ec4899', '#14b8a6',
];

/* ── Chart registry ─────────────────────────────────────── */
const _charts = {};

function destroyChart(id) {
  if (_charts[id]) {
    try { _charts[id].destroy(); } catch (_) {}
    delete _charts[id];
  }
}

/* ── Entry point called from dashboard.js ───────────────── */
function buildCharts(data) {
  // Small delay so the DOM tab panel is fully visible before Chart.js
  // measures container dimensions
  setTimeout(() => {
    buildStatusChart(data.status_distribution    || {});
    buildFoodTypeChart(data.food_type_frequency  || {});
    buildTrendChart(data.freshness_trend         || []);
    buildAvgFreshnessChart(data.food_sensor_averages || {});
  }, 80);
}
window.buildCharts = buildCharts;

/* ── 1. Status Distribution — Doughnut ──────────────────── */
function buildStatusChart(dist) {
  destroyChart('statusChart');
  const canvas = document.getElementById('statusChart');
  if (!canvas) return;

  const entries = Object.entries(dist).filter(([, v]) => v > 0);
  if (!entries.length) { renderEmpty(canvas, 'No data yet'); return; }

  const labels = entries.map(([k]) => capitalise(k));
  const values = entries.map(([, v]) => v);
  const colors = entries.map(([k]) => STATUS_COLORS[k] || STATUS_COLORS.unknown);

  _charts.statusChart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors.map(c => c + 'cc'),
        borderColor:     colors,
        borderWidth:     2,
        hoverOffset:     8,
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      cutout:              '64%',
      animation:           { duration: 600 },
      plugins: {
        legend: { position: 'right', labels: { boxWidth: 10 } },
        tooltip: {
          callbacks: {
            label: ctx => {
              const total = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
              const pct   = total ? ((ctx.raw / total) * 100).toFixed(0) : 0;
              return `  ${ctx.label}: ${ctx.raw} (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

/* ── 2. Food Type Frequency — Horizontal Bar ────────────── */
function buildFoodTypeChart(freq) {
  destroyChart('foodTypeChart');
  const canvas = document.getElementById('foodTypeChart');
  if (!canvas) return;

  const entries = Object.entries(freq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);
  if (!entries.length) { renderEmpty(canvas, 'No data yet'); return; }

  const labels = entries.map(([k]) => capitalise(k.replace(/_/g, ' ')));
  const values = entries.map(([, v]) => v);

  _charts.foodTypeChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label:           'Predictions',
        data:            values,
        backgroundColor: CHART_PALETTE.map(c => c + '99').slice(0, entries.length),
        borderColor:     CHART_PALETTE.slice(0, entries.length),
        borderWidth:     2,
        borderRadius:    6,
        hoverBackgroundColor: CHART_PALETTE.slice(0, entries.length),
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      indexAxis:           'y',
      animation:           { duration: 600 },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => `  ${ctx.raw} prediction${ctx.raw !== 1 ? 's' : ''}` } },
      },
      scales: {
        x: {
          grid:        { color: 'rgba(255,255,255,0.04)' },
          ticks:       { color: '#94a3b8', stepSize: 1 },
          beginAtZero: true,
        },
        y: {
          grid:  { display: false },
          ticks: { color: '#94a3b8', font: { size: 11 } },
        },
      },
    },
  });
}

/* ── 3. Freshness Trend — Line ──────────────────────────── */
function buildTrendChart(trend) {
  destroyChart('trendChart');
  const canvas = document.getElementById('trendChart');
  if (!canvas) return;

  if (!trend.length) { renderEmpty(canvas, 'No trend data yet'); return; }

  // Build time-stamped labels, de-duplicate if many share the same date
  const labels = trend.map((t, i) => {
    try { return new Date(t.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch (_) { return `#${i + 1}`; }
  });
  const values = trend.map(t => +(t.freshness || 0));
  const ptColors = values.map(v => v >= 70 ? '#10b981' : v >= 40 ? '#f59e0b' : '#ef4444');

  _charts.trendChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label:              'Freshness %',
        data:               values,
        borderColor:        '#00d4aa',
        backgroundColor:    'rgba(0,212,170,0.08)',
        pointBackgroundColor: ptColors,
        pointBorderColor:   ptColors,
        pointRadius:        5,
        pointHoverRadius:   8,
        fill:               true,
        tension:            0.35,
        borderWidth:        2.5,
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      animation:           { duration: 700 },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => `  Freshness: ${ctx.raw.toFixed(0)}%` } },
      },
      scales: {
        y: {
          min:   0,
          max:   100,
          grid:  { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#94a3b8', callback: v => v + '%' },
        },
        x: {
          grid:  { display: false },
          ticks: {
            color:        '#94a3b8',
            maxTicksLimit: 8,
            maxRotation:  30,
          },
        },
      },
    },
  });
}

/* ── 4. Avg Freshness by Food Type — Bar ────────────────── */
function buildAvgFreshnessChart(foodAvgs) {
  destroyChart('radarChart');
  const canvas = document.getElementById('radarChart');
  if (!canvas) return;

  const entries = Object.entries(foodAvgs)
    .filter(([, v]) => v.count >= 1)
    .sort((a, b) => b[1].avg_freshness - a[1].avg_freshness)
    .slice(0, 8);

  if (entries.length < 1) { renderEmpty(canvas, 'Make 2+ predictions to compare'); return; }

  const labels = entries.map(([k]) => capitalise(k.replace(/_/g, ' ')));
  const values = entries.map(([, v]) => +(v.avg_freshness || 0));
  const bgColors = values.map(v =>
    v >= 70 ? '#10b98190' : v >= 40 ? '#f59e0b90' : '#ef444490');
  const bdColors = values.map(v =>
    v >= 70 ? '#10b981'   : v >= 40 ? '#f59e0b'   : '#ef4444');

  _charts.radarChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label:           'Avg Freshness %',
        data:            values,
        backgroundColor: bgColors,
        borderColor:     bdColors,
        borderWidth:     2,
        borderRadius:    6,
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      animation:           { duration: 600 },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => `  Avg freshness: ${ctx.raw.toFixed(1)}%` } },
      },
      scales: {
        y: {
          min:   0,
          max:   100,
          grid:  { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#94a3b8', callback: v => v + '%' },
        },
        x: {
          grid:  { display: false },
          ticks: { color: '#94a3b8', font: { size: 10 }, maxRotation: 30 },
        },
      },
    },
  });
}

/* ── Helpers ────────────────────────────────────────────── */
function capitalise(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
}

function renderEmpty(canvas, msg) {
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle    = '#475569';
  ctx.font         = '13px Inter, system-ui';
  ctx.textAlign    = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(msg, canvas.width / 2, canvas.height / 2);
}
