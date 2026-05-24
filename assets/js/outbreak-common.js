// Shared helpers for the outbreak dashboards (ebola, hanta).
// Holds the parts that are byte-identical between dashboards: the JSON
// loader, the "last updated" meta, and the entire news-feed system.
// Per-disease logic (severity classification, official-source list,
// stat cards, maps, charts) stays in each dashboard's own app.js.

async function loadJSON(p) { return (await fetch(p)).json(); }

function renderMeta(data) {
  document.getElementById('last-updated').textContent = 'Updated ' + data.last_updated;
  var r = document.getElementById('methodology-reviewed');
  if (r) r.textContent = data.last_updated;
  var f = document.getElementById('footer-updated');
  if (f) f.textContent = 'Last updated: ' + data.last_updated;
}

var sevLabels = { alert: 'Alert', advisory: 'Advisory', update: 'Update', background: 'Info' };

// `classify` maps an article -> severity key; `officialSources` is the list
// of source names treated as official (everything else is "media").
function renderNewsFeed(data, filter, classify, officialSources) {
  var allArticles = data.articles;
  var feed = document.getElementById('news-feed');
  if (!feed) return;
  feed.innerHTML = '';

  var filtered = allArticles;
  if (filter && filter !== 'all') {
    if (filter === 'media') {
      filtered = allArticles.filter(function(a) { return officialSources.indexOf(a.source) === -1; });
    } else {
      filtered = allArticles.filter(function(a) { return a.source === filter; });
    }
  }

  var VIS = 5;
  filtered.forEach(function(a, i) {
    var sev = classify(a);
    var card = document.createElement('div');
    card.className = 'news-card' + (i >= VIS ? ' news-hidden' : '');
    card.innerHTML =
      '<div class="news-card-header">' +
        '<span class="news-date">' + a.date + '</span>' +
        '<span class="news-source-badge">' + a.source + '</span>' +
        '<span class="news-sev-badge sev-' + sev + '">' + sevLabels[sev] + '</span>' +
      '</div>' +
      '<a href="' + a.url + '" target="_blank" rel="noopener" class="news-headline">' + a.title + '</a>' +
      (a.summary ? '<div class="news-summary-text">' + a.summary + '</div>' : '');
    feed.appendChild(card);
  });

  var existing = feed.parentElement.querySelector('.news-show-more');
  if (existing) existing.remove();

  if (filtered.length > VIS) {
    var btn = document.createElement('button');
    btn.className = 'news-show-more';
    btn.textContent = 'Show ' + (filtered.length - VIS) + ' older updates';
    btn.onclick = function() {
      var h = feed.querySelectorAll('.news-hidden');
      for (var j = 0; j < h.length; j++) h[j].classList.remove('news-hidden');
      btn.remove();
    };
    feed.parentElement.appendChild(btn);
  }
}

function initFilterTabs(newsData, classify, officialSources) {
  var tabs = document.querySelectorAll('.filter-tab');
  tabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      tabs.forEach(function(t) { t.classList.remove('active'); });
      tab.classList.add('active');
      renderNewsFeed(newsData, tab.dataset.filter, classify, officialSources);
    });
  });
}

// ── Leaflet map factory ───────────────────────────────────────────────────────
// The map creation, CARTO basemap, and reset-button wiring are identical across
// dashboards; only the bounds/zoom differ. Each dashboard calls this, then adds
// its own disease-specific markers to the returned map instance.
function createOutbreakMap(elId, opts) {
  var map = L.map(elId, {
    scrollWheelZoom: false,
    zoomControl: true,
    tap: false,
    dragging: !L.Browser.mobile,
    touchZoom: true,
    maxBounds: opts.maxBounds,
    maxBoundsViscosity: 1.0
  });

  map.fitBounds(opts.defaultBounds, { padding: [20, 20], maxZoom: opts.fitMaxZoom });

  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);

  var resetBtn = document.getElementById('map-reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', function() {
      map.fitBounds(opts.defaultBounds, { padding: [20, 20], maxZoom: opts.fitMaxZoom });
    });
  }

  return map;
}

// ── Chart.js factories ────────────────────────────────────────────────────────
// The Chart.js option scaffold (bottom legend, non-aspect-ratio responsive, axis
// fonts) is identical across dashboards; only the datasets, time unit, grid color,
// and annotations differ. Each dashboard builds its own datasets and passes the
// per-disease bits in `opts`.
var OUTBREAK_LEGEND = { position: 'bottom', labels: { font: { family: 'Inter', size: 12 }, boxWidth: 12, padding: 16 } };

function makeTimeSeriesChart(elId, type, datasets, opts) {
  var el = document.getElementById(elId);
  if (!el) return null;
  opts = opts || {};
  var yScale = { beginAtZero: true, ticks: { font: { family: 'Inter', size: 12 } }, grid: { color: opts.gridColor } };
  if (opts.yTitle) {
    yScale.title = { display: true, text: opts.yTitle, font: { family: 'Inter', size: 12 } };
  }
  var plugins = { legend: OUTBREAK_LEGEND };
  if (opts.annotations) plugins.annotation = opts.annotations;
  return new Chart(el.getContext('2d'), {
    type: type,
    data: { datasets: datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: plugins,
      scales: {
        x: {
          type: 'time',
          time: { unit: opts.xUnit, displayFormats: opts.xFormats, tooltipFormat: 'MMM d, yyyy' },
          ticks: { font: { family: 'Inter', size: 12 }, maxTicksLimit: opts.maxTicks },
          grid: { display: false }
        },
        y: yScale
      }
    }
  });
}

// `events` is a small per-disease array of { date: 'YYYY-MM-DD', color, label }.
// Returns a Chart.js annotation plugin config (the object you'd pass directly to
// chart options.plugins.annotation). Each event becomes a dashed vertical line
// with its label tucked into the upper-left, identical styling across dashboards.
function buildEventAnnotations(events) {
  var annotations = {};
  events.forEach(function(e, i) {
    annotations['a' + (i + 1)] = {
      type: 'line', scaleID: 'x',
      value: new Date(e.date).getTime(),
      borderColor: e.color, borderWidth: 1, borderDash: [4, 4],
      label: { display: true, content: e.label, position: 'start', yAdjust: -12,
        font: { size: 10, family: 'Inter' }, color: e.color, backgroundColor: 'rgba(255,255,255,0.85)', padding: 3 }
    };
  });
  return { annotations: annotations };
}

// ── Stat-card factories ───────────────────────────────────────────────────────
// Three families of cards appear on every dashboard. Each twin builds an array
// of {val, label, sub, …} items from its disease-specific JSON and passes it in;
// the shared renderer handles the markup. Markup is byte-identical to the old
// per-twin functions.

// Hero strip: <div class="stat-chip {cls}"> with numeric or string value.
function renderStatChips(elId, chips) {
  var el = document.getElementById(elId);
  if (!el) return;
  el.innerHTML = chips.map(function(c) {
    var val = typeof c.val === 'number' ? c.val.toLocaleString() : c.val;
    return '<div class="stat-chip ' + c.cls + '">' +
      '<span class="stat-value">' + val + '</span>' +
      '<span class="stat-label">' + c.label + '</span>' +
      (c.sub ? '<span class="stat-sub ' + (c.subCls || '') + '">' + c.sub + '</span>' : '') +
      '</div>';
  }).join('');
}

// Grid of big stat cards, optionally with a weekly delta. Each card may set
// `zeroLabel` to override the rendering when delta === 0 (e.g. Ebola uses
// "No change this week" for every card; Hanta uses "No new deaths this week"
// only on the deaths card).
function renderDeltaStatCards(elId, cards) {
  var el = document.getElementById(elId);
  if (!el) return;
  el.innerHTML = cards.map(function(c) {
    var deltaHtml = '';
    if (c.delta !== null && c.delta !== undefined) {
      if (c.delta === 0 && c.zeroLabel) {
        deltaHtml = '<div class="delta delta-flat">' + c.zeroLabel + '</div>';
      } else {
        var cls = c.delta > 0 ? 'delta-up' : c.delta < 0 ? 'delta-down' : 'delta-flat';
        deltaHtml = '<div class="delta ' + cls + '">' + (c.delta > 0 ? '+' : '') + c.delta + ' this week</div>';
      }
    }
    return '<div class="stat-card ' + c.cls + '">' +
      '<div class="stat-value">' + c.val.toLocaleString() + '</div>' +
      deltaHtml +
      '<div class="stat-label">' + c.label + '</div>' +
      '<div class="stat-sub">' + c.sub + '</div>' +
      '</div>';
  }).join('');
}

// Compact metric strip used inside the cluster/outbreak detail card.
// ── Outcome classification ───────────────────────────────────────────────────
// Each twin passes its own keyword -> {cls, sym} map. The first keyword whose
// lowercased substring is found in the outcome string wins; if nothing matches,
// the `unknown` entry is used. Pulling this out of per-twin app.js keeps the
// outcome vocabulary in one place and lets a new outbreak add its own keywords
// without re-implementing the loop.
function classifyOutcome(outcome, keywordMap) {
  var lo = (outcome || '').toLowerCase();
  for (var i = 0; i < keywordMap.keywords.length; i++) {
    var entry = keywordMap.keywords[i];
    for (var j = 0; j < entry.match.length; j++) {
      if (lo.indexOf(entry.match[j]) !== -1) return { cls: entry.cls, sym: entry.sym };
    }
  }
  return keywordMap.unknown;
}

function renderMetricGrid(elId, metrics) {
  var el = document.getElementById(elId);
  if (!el) return;
  el.innerHTML = metrics.map(function(m) {
    return '<div class="metric"><span class="metric-val">' + m.v + '</span><span class="metric-lbl">' + m.l + '</span></div>';
  }).join('');
}

function makeCategoryBarChart(elId, labels, datasets, opts) {
  var el = document.getElementById(elId);
  if (!el) return null;
  opts = opts || {};
  return new Chart(el.getContext('2d'), {
    type: 'bar',
    data: { labels: labels, datasets: datasets },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: OUTBREAK_LEGEND },
      scales: {
        x: { beginAtZero: true, ticks: { font: { family: 'Inter', size: 12 } }, grid: { color: opts.gridColor } },
        y: { ticks: { font: { family: 'Inter', size: 12 } }, grid: { display: false } }
      }
    }
  });
}
