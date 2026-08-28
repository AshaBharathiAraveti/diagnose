/**
 * FreshSense Dashboard — Main JavaScript
 */

const API = 'http://localhost:5000/api';

// ─── State ────────────────────────────────────────────────────────────────────
let currentTab   = 'dashboard';
let historyPage  = 1;
let historyPages = 1;
let _lastRecordId = null;

// ─── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initFoodTypeDropdown();
  checkModelStatus();
  refreshDashboard();
  updateSensorBars();
  switchTab('dashboard');
  // Auto-refresh every 10s to show live ESP32 results
  setInterval(() => {
    if (currentTab === 'dashboard') refreshDashboard();
  }, 10000);
});

// ─── Tab navigation ────────────────────────────────────────────────────────────
function switchTab(tab) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const panel = document.getElementById('tab-' + tab);
  const nav   = document.getElementById('nav-' + tab);
  if (panel) panel.classList.add('active');
  if (nav)   nav.classList.add('active');
  currentTab = tab;
  if (tab === 'history')   loadHistory();
  if (tab === 'analytics') loadAnalytics();
  if (tab === 'dashboard') refreshDashboard();
  if (tab === 'predict')   fillFromESP32(false); // auto-fill silently
}
window.switchTab = switchTab;

// ─── Model status ──────────────────────────────────────────────────────────────
async function checkModelStatus() {
  try {
    const res  = await fetch(API + '/models/status');
    const data = await res.json();
    const fm   = data?.data?.freshness_model;
    const fDot = document.querySelector('#freshnessBadge .badge-dot');
    if (fDot) fDot.className = `badge-dot ${fm?.is_loaded ? 'online' : 'offline'}`;
  } catch (_) {}
  setTimeout(checkModelStatus, 15000);
}

// ─── Food type dropdown ────────────────────────────────────────────────────────
async function initFoodTypeDropdown() {
  const sel             = document.getElementById('foodType');
  const histFoodFilter  = document.getElementById('historyFoodFilter');
  try {
    const res  = await fetch(API + '/food-types');
    const data = await res.json();
    const cats = data?.data?.categories || {};
    const allTypes = [];

    Object.entries(cats).forEach(([catName, cat]) => {
      const og = document.createElement('optgroup');
      og.label = cat.icon ? `${cat.icon} ${catName}` : catName;
      (cat.items || []).forEach(ft => {
        const opt = document.createElement('option');
        opt.value = ft;
        opt.textContent = ft.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        og.appendChild(opt);
        allTypes.push(ft);
      });
      if (sel) sel.appendChild(og.cloneNode(true));
    });

    if (histFoodFilter) {
      allTypes.forEach(ft => {
        const o = document.createElement('option');
        o.value = ft;
        o.textContent = ft.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        histFoodFilter.appendChild(o);
      });
    }

    if (sel) {
      sel.addEventListener('change', () => {
        const hint = document.getElementById('foodTypeHint');
        if (hint) hint.textContent = sel.value
          ? `Selected: ${sel.value.replace(/_/g, ' ')}`
          : '';
      });
    }
  } catch (e) {
    console.error('Food types error:', e);
  }
}

// ─── Sensor slider sync ────────────────────────────────────────────────────────
function syncInput(sliderId, inputId) {
  const s = document.getElementById(sliderId), i = document.getElementById(inputId);
  if (s && i) { i.value = s.value; updateSensorBars(); }
}
function syncSlider(inputId, sliderId) {
  const i = document.getElementById(inputId), s = document.getElementById(sliderId);
  if (i && s) { s.value = i.value; updateSensorBars(); }
}
function updateSensorBars() {
  const temp  = parseFloat(document.getElementById('temperatureInput')?.value ?? 5);
  const humid = parseFloat(document.getElementById('humidityInput')?.value ?? 70);
  const gas   = parseFloat(document.getElementById('gasInput')?.value ?? 0.3);
  setBar('tempBar',  ((temp + 20) / 70) * 100);
  setBar('humidBar', humid);
  setBar('gasBar',   (gas / 2) * 100);
}
function setBar(id, pct) {
  const el = document.getElementById(id);
  if (el) el.style.width = Math.min(100, Math.max(0, pct)) + '%';
}
window.syncInput     = syncInput;
window.syncSlider    = syncSlider;

// ─── ESP32 Auto-fill for Predict Tab ──────────────────────────────────────────
/**
 * Fetches the latest ESP32 sensor reading and populates the predict form.
 * @param {boolean} showFeedback  If true, show toast messages to the user.
 */
async function fillFromESP32(showFeedback = true) {
  const btn = document.getElementById('esp32FillBtn');
  if (btn) { btn.disabled = true; btn.textContent = '📡 Reading…'; }

  try {
    const res = await fetch(API + '/latest');
    const lat = await res.json();

    if (!lat || Object.keys(lat).length === 0) {
      if (showFeedback) showToast('No ESP32 data yet — send at least one reading first.', 'error');
      if (btn) { btn.disabled = false; btn.textContent = '📡 Read from ESP32'; }
      return;
    }

    const temp  = lat.temperature ?? null;
    const humid = lat.humidity    ?? null;
    const gas   = lat.gas         ?? null;

    if (temp !== null) {
      const tI = document.getElementById('temperatureInput');
      const tS = document.getElementById('tempSlider');
      if (tI) tI.value = temp;
      if (tS) tS.value = temp;
    }
    if (humid !== null) {
      const hI = document.getElementById('humidityInput');
      const hS = document.getElementById('humidSlider');
      if (hI) hI.value = humid;
      if (hS) hS.value = humid;
    }
    if (gas !== null) {
      const gI = document.getElementById('gasInput');
      const gS = document.getElementById('gasSlider');
      if (gI) gI.value = gas;
      if (gS) gS.value = gas;
    }

    updateSensorBars();

    // Update the badge under the button
    const badge = document.getElementById('esp32FillBadge');
    if (badge) {
      const ago = lat.timestamp ? _relativeTime(new Date(lat.timestamp)) : 'just now';
      badge.textContent = `📡 ESP32 data loaded · ${ago}`;
      badge.style.display = 'inline-block';
    }

    if (showFeedback) showToast(`Loaded from ESP32 — Temp: ${temp}°C  Humidity: ${humid}%  Gas: ${gas}`, 'success');
  } catch (err) {
    if (showFeedback) showToast('Could not reach backend: ' + err.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '📡 Read from ESP32'; }
  }
}
window.fillFromESP32 = fillFromESP32;

// ─── Prediction ────────────────────────────────────────────────────────────────
async function submitPrediction(e) {
  e.preventDefault();
  const foodType    = document.getElementById('foodType').value;
  const temperature = parseFloat(document.getElementById('temperatureInput').value);
  const humidity    = parseFloat(document.getElementById('humidityInput').value);
  const gas         = parseFloat(document.getElementById('gasInput').value);

  if (!foodType)                             { showToast('Please select a food type', 'error'); return; }
  if (isNaN(temperature) || isNaN(humidity) || isNaN(gas)) { showToast('Please fill in all sensor values', 'error'); return; }

  showLoading('Analysing freshness with ML model…');
  try {
    const res  = await fetch(API + '/predict/freshness', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ food_type: foodType, temperature, humidity, gas })
    });
    const json = await res.json();
    hideLoading();

    if (json.success) {
      // Flatten nested data
      const inner = json.data?.data ?? json.data ?? {};
      const pred  = inner.success ? inner : (inner.fallback_prediction || inner);

      const status   = normaliseStatus(pred.predicted_status ?? pred.fallback_prediction?.predicted_status ?? '—');
      const conf     = pred.confidence        ?? pred.fallback_prediction?.confidence        ?? 0;
      const days     = pred.predicted_remaining_days ?? pred.fallback_prediction?.predicted_remaining_days ?? 0;
      const freshPct = pred.freshness_percentage     ?? pred.fallback_prediction?.freshness_percentage     ?? 0;
      const recs     = pred.recommendations          ?? pred.fallback_prediction?.recommendations          ?? {};

      showResultPanel(foodType, status, conf, days, freshPct, recs);
      showToast('Prediction complete!', 'success');
      setTimeout(refreshDashboard, 700);
    } else {
      showToast(json.error || 'Prediction failed', 'error');
    }
  } catch (err) {
    hideLoading();
    showToast('Network error: ' + err.message, 'error');
  }
}
window.submitPrediction = submitPrediction;

function normaliseStatus(s) {
  // Map raw binary '0'/'1' to proper labels
  if (s === '0' || s === 0) return 'fresh';
  if (s === '1' || s === 1) return 'spoiled';
  return s || '—';
}

function showResultPanel(foodType, status, conf, days, freshPct, recs) {
  const panel = document.getElementById('resultPanel');
  if (!panel) return;
  panel.style.display = 'block';

  document.getElementById('resultFoodBadge').textContent = foodType.replace(/_/g, ' ');
  document.getElementById('resultPct').textContent       = freshPct.toFixed(0) + '%';
  document.getElementById('resultDays').textContent      = Number(days).toFixed(1);
  document.getElementById('resultConf').textContent      = (conf * 100).toFixed(0) + '%';

  const statusEl = document.getElementById('resultStatusBig');
  statusEl.textContent = status.toUpperCase();
  statusEl.className   = `result-status-badge bg-${status}`;

  drawGauge('resultGauge', freshPct, status);

  // Recommendations
  const recBox  = document.getElementById('recommendationsBox');
  const recList = document.getElementById('recommendationsList');
  recList.innerHTML = '';
  const items = Array.isArray(recs?.recommendations) ? recs.recommendations :
    (typeof recs === 'object' ? recs.recommendations : []) || [];
  items.forEach(r => {
    const li = document.createElement('li');
    li.textContent = r;
    recList.appendChild(li);
  });
  if (recBox) recBox.style.display = items.length ? 'block' : 'none';
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ─── Dashboard ─────────────────────────────────────────────────────────────────
async function refreshDashboard() {
  const icon = document.getElementById('refreshIcon');
  if (icon) { icon.style.animation = 'spin 0.8s linear infinite'; setTimeout(() => icon.style.animation = '', 1200); }

  try {
    // Analytics summary
    const anaRes = await fetch(API + '/analytics');
    const ana    = await anaRes.json();
    if (ana.success && ana.data && !ana.data.empty) {
      const s = ana.data.summary;
      setText('statTotalVal',  s.total_predictions);
      setText('statSpoiledVal', s.spoilage_rate + '%');
      setText('statFreshVal',  s.avg_freshness  + '%');
      setText('statDaysVal',   s.avg_remaining_days + 'd');
      setText('aTotalVal',  s.total_predictions);
      setText('aSpoileVal', s.spoilage_rate + '%');
      setText('aFreshVal',  s.avg_freshness  + '%');
      setText('aDaysVal',   s.avg_remaining_days + 'd');
    }

    // Latest record
    const latRes = await fetch(API + '/latest');
    const lat    = await latRes.json();
    if (lat && Object.keys(lat).length > 0) {
      document.getElementById('latestCard').style.display     = 'block';
      document.getElementById('dashboardEmpty').style.display = 'none';

      // Show LIVE indicator if a new record arrived
      const liveEl  = document.getElementById('liveIndicator');
      const iotDot  = document.getElementById('iotDot');
      const iotText = document.getElementById('iotBadgeText');
      if (lat.id !== _lastRecordId) {
        _lastRecordId = lat.id;
        if (liveEl)  liveEl.style.display = 'flex';
        if (iotDot)  iotDot.className = 'badge-dot online';
        if (iotText) iotText.textContent = 'ESP32 Live';
        setTimeout(() => { if (liveEl) liveEl.style.display = 'none'; }, 4000);
      }

      const status = normaliseStatus(lat.ml_predicted_status);
      setText('latestFood',      (lat.food_type || '—').replace(/_/g, ' '));
      setText('latestDays',      (+(lat.ml_predicted_days || 0)).toFixed(1) + ' days');
      setText('latestConf',      ((lat.ml_confidence || 0) * 100).toFixed(0) + '%');
      setText('latestTemp',      (lat.temperature ?? '—') + ' °C');
      setText('latestHumidity',  (lat.humidity    ?? '—') + ' %');
      setText('latestGas',       (lat.gas         ?? '—') + ' ppm');
      setText('latestTimestamp', lat.timestamp ? new Date(lat.timestamp).toLocaleString() : '—');

      const statusEl = document.getElementById('latestStatus');
      if (statusEl) {
        statusEl.textContent   = status;
        statusEl.className     = `detail-value status-badge bg-${status}`;
        statusEl.style.cssText = 'display:inline-block;padding:3px 10px;border-radius:100px;font-size:0.8rem;font-weight:700;';
      }

      const freshPct = lat.ml_freshness_percentage || 0;
      setText('gaugePct', freshPct.toFixed(0) + '%');
      drawGauge('gaugeCanvas', freshPct, status);

      // ── Update ESP32 Live Feed card ──────────────────────────
      updateLiveFeed(lat, status, freshPct);
    } else {
      document.getElementById('latestCard').style.display     = 'none';
      document.getElementById('dashboardEmpty').style.display = 'block';
    }
  } catch (e) {
    console.error('Dashboard error:', e);
  }
}
window.refreshDashboard = refreshDashboard;

// ─── History ───────────────────────────────────────────────────────────────────
async function loadHistory() {
  const food   = document.getElementById('historyFoodFilter')?.value   || '';
  const status = document.getElementById('historyStatusFilter')?.value || '';
  const params = new URLSearchParams({ page: historyPage, per_page: 15, food_type: food, status });

  try {
    const res  = await fetch(`${API}/history?${params}`);
    const json = await res.json();
    const rows = json.data || [];
    const pag  = json.pagination || {};
    historyPages = pag.pages || 1;

    const tbody = document.getElementById('historyBody');
    if (!tbody) return;

    tbody.innerHTML = rows.length === 0
      ? '<tr><td colspan="9" class="table-empty">No records found</td></tr>'
      : rows.map(r => {
          const st = normaliseStatus(r.ml_predicted_status);
          return `<tr>
            <td><strong>${(r.food_type || '—').replace(/_/g, ' ')}</strong></td>
            <td><span class="status-pill bg-${st}">${st}</span></td>
            <td>${(+(r.ml_freshness_percentage || 0)).toFixed(0)}%</td>
            <td>${(+(r.ml_predicted_days || 0)).toFixed(1)}</td>
            <td>${r.temperature ?? '—'}°</td>
            <td>${r.humidity    ?? '—'}%</td>
            <td>${r.gas        ?? '—'}</td>
            <td>${((r.ml_confidence || 0) * 100).toFixed(0)}%</td>
            <td>${r.timestamp ? new Date(r.timestamp).toLocaleString() : '—'}</td>
          </tr>`;
        }).join('');

    setText('pageInfo', `Page ${historyPage} of ${historyPages}`);
    const prev = document.getElementById('prevPageBtn');
    const next = document.getElementById('nextPageBtn');
    if (prev) prev.disabled = historyPage <= 1;
    if (next) next.disabled = historyPage >= historyPages;
  } catch (e) {
    console.error('History error:', e);
  }
}
window.loadHistory = loadHistory;

function changePage(delta) {
  const p = historyPage + delta;
  if (p >= 1 && p <= historyPages) { historyPage = p; loadHistory(); }
}
window.changePage = changePage;

async function clearHistory() {
  if (!confirm('Clear all prediction history? This cannot be undone.')) return;
  try {
    await fetch(API + '/clear-history', { method: 'DELETE' });
    showToast('History cleared', 'info');
    historyPage = 1;
    loadHistory();
    refreshDashboard();
  } catch (e) { showToast('Error clearing history', 'error'); }
}
window.clearHistory = clearHistory;

// ─── Analytics ─────────────────────────────────────────────────────────────────
async function loadAnalytics() {
  try {
    const res  = await fetch(API + '/analytics');
    const json = await res.json();

    const emptyEl = document.getElementById('analyticsEmpty');

    if (!json.success) {
      if (emptyEl) emptyEl.style.display = 'block';
      return;
    }

    const d = json.data;
    // "empty" flag is only set explicitly when there are 0 rows
    if (d.empty === true) {
      if (emptyEl) emptyEl.style.display = 'block';
      return;
    }
    if (emptyEl) emptyEl.style.display = 'none';

    // Normalise status keys ('0' → 'fresh', '1' → 'spoiled')
    const rawDist = d.status_distribution || {};
    const normDist = {};
    Object.entries(rawDist).forEach(([k, v]) => {
      const key = normaliseStatus(k);
      normDist[key] = (normDist[key] || 0) + v;
    });

    const s = d.summary || {};
    setText('aTotalVal',  s.total_predictions ?? 0);
    setText('aSpoileVal', (s.spoilage_rate ?? 0) + '%');
    setText('aFreshVal',  (s.avg_freshness  ?? 0) + '%');
    setText('aDaysVal',   (s.avg_remaining_days ?? 0) + 'd');

    // Delegate chart rendering to charts.js
    if (typeof buildCharts === 'function') {
      buildCharts({ ...d, status_distribution: normDist });
    }
  } catch (e) {
    console.error('Analytics error:', e);
  }
}
window.loadAnalytics = loadAnalytics;

// ─── ESP32 Live Feed Card ──────────────────────────────────────────────────────
function updateLiveFeed(lat, status, freshPct) {
  const noData    = document.getElementById('esp32NoData');
  const resultRow = document.getElementById('esp32ResultRow');
  const dot       = document.getElementById('esp32FeedDot');
  const statusTxt = document.getElementById('esp32FeedStatus');

  // Sensor tiles
  setText('feedTemp',  (lat.temperature ?? '—') + '°');
  setText('feedHumid', (lat.humidity    ?? '—') + '%');
  setText('feedGas',   (lat.gas         ?? '—'));
  setText('feedFood',  (lat.food_type   ?? '—').replace(/_/g, ' '));

  // Connection badge
  if (dot)       { dot.className = 'badge-dot online'; }
  if (statusTxt) {
    const ago = lat.timestamp
      ? _relativeTime(new Date(lat.timestamp))
      : 'just now';
    statusTxt.textContent = `ESP32 Connected · ${ago}`;
  }

  // Result row
  if (noData)    noData.style.display    = 'none';
  if (resultRow) resultRow.style.display = 'flex';

  // Mini gauge
  drawGauge('feedGauge', freshPct, status);
  setText('feedGaugePct', freshPct.toFixed(0) + '%');

  // Status badge
  const badge = document.getElementById('feedStatusBadge');
  if (badge) {
    badge.textContent = status.toUpperCase();
    badge.className   = `esp32-result-status bg-${status}`;
  }

  setText('feedDays', (+(lat.ml_predicted_days || 0)).toFixed(1));
  setText('feedConf', ((lat.ml_confidence || 0) * 100).toFixed(0) + '%');
  setText('feedTime',  lat.timestamp ? new Date(lat.timestamp).toLocaleTimeString() : '—');
}

function _relativeTime(date) {
  const diffSec = Math.round((Date.now() - date.getTime()) / 1000);
  if (diffSec < 5)   return 'just now';
  if (diffSec < 60)  return `${diffSec}s ago`;
  if (diffSec < 3600) return `${Math.round(diffSec / 60)}m ago`;
  return `${Math.round(diffSec / 3600)}h ago`;
}

// ─── Gauge ──────────────────────────────────────────────────────────────────────
function drawGauge(canvasId, pct, status) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2 + 10;
  const r  = Math.min(W, H) / 2 - 18;

  const COLORS = {
    fresh: '#10b981', good: '#34d399', moderate: '#f59e0b',
    spoiling: '#f97316', spoiled: '#ef4444'
  };
  const color = COLORS[status] || '#475569';

  const start = Math.PI * 0.75;
  const end   = start + Math.PI * 1.5 * Math.min(100, Math.max(0, pct)) / 100;

  ctx.clearRect(0, 0, W, H);

  // Background arc
  ctx.beginPath();
  ctx.arc(cx, cy, r, start, start + Math.PI * 1.5);
  ctx.strokeStyle = 'rgba(255,255,255,0.08)';
  ctx.lineWidth   = 14;
  ctx.lineCap     = 'round';
  ctx.stroke();

  // Value arc with glow
  if (pct > 0) {
    ctx.beginPath();
    ctx.arc(cx, cy, r, start, end);
    ctx.strokeStyle  = color;
    ctx.lineWidth    = 14;
    ctx.lineCap      = 'round';
    ctx.shadowColor  = color;
    ctx.shadowBlur   = 18;
    ctx.stroke();
    ctx.shadowBlur   = 0;
  }
}

// ─── Utilities ─────────────────────────────────────────────────────────────────
function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val ?? '—';
}
function showLoading(msg) {
  setText('loadingText', msg || 'Loading…');
  document.getElementById('loadingOverlay').style.display = 'flex';
}
function hideLoading() {
  document.getElementById('loadingOverlay').style.display = 'none';
}

let _toastTimer;
function showToast(msg, type = 'info') {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className   = `toast ${type} show`;
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => t.classList.remove('show'), 3500);
}
