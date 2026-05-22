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
