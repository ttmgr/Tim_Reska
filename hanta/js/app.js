async function loadJSON(p) { return (await fetch(p)).json(); }

function renderHeroStats(data, hondius) {
  var h = hondius || {};
  var chips = [
    { val: h.total_cases || '--', label: 'Ship cases', sub: 'MV Hondius cluster', cls: 'blue', subCls: '' },
    { val: h.total_deaths || '--', label: 'Ship deaths', sub: 'All passengers aged 57-68', cls: 'red', subCls: '' },
    { val: (h.cfr_percent || '--') + '%', label: 'Ship CFR', sub: 'Case fatality rate', cls: 'red', subCls: '' },
    { val: 'Quarantined', label: 'Status', sub: 'En route Tenerife', cls: 'default', subCls: '' }
  ];
  var el = document.getElementById('hero-stats');
  if (!el) return;
  el.innerHTML = chips.map(function(c) {
    return '<div class="stat-chip ' + c.cls + '">' +
      '<span class="stat-value">' + c.val.toLocaleString() + '</span>' +
      '<span class="stat-label">' + c.label + '</span>' +
      (c.sub ? '<span class="stat-sub ' + c.subCls + '">' + c.sub + '</span>' : '') +
      '</div>';
  }).join('');
}

function renderStatGrid(data) {
  var s = data.summary;
  var d = s.weekly_delta || {};
  var cards = [
    { val: s.total_cases_2026, label: 'Global total cases', sub: 'All 2026 reported cases worldwide', delta: d.cases, type: 'cases', cls: 'blue-top' },
    { val: s.total_deaths_2026, label: 'Global total deaths', sub: 'Global CFR: ' + s.cfr_percent + '%', delta: d.deaths, type: 'deaths', cls: 'red-top' },
    { val: s.countries_affected, label: 'Countries affected', sub: 'Cases or contact tracing', delta: null, cls: '' },
    { val: s.active_clusters, label: 'Active clusters', sub: 'MV Hondius (ANDV)', delta: null, cls: 'amber-top' }
  ];
  var el = document.getElementById('stat-grid');
  if (!el) return;
  el.innerHTML = cards.map(function(c) {
    var deltaHtml = '';
    if (c.delta !== null && c.delta !== undefined) {
      if (c.delta === 0 && c.type === 'deaths') deltaHtml = '<div class="delta delta-flat">No new deaths this week</div>';
      else {
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

function renderMeta(data) {
  document.getElementById('last-updated').textContent = 'Updated ' + data.last_updated;
  var r = document.getElementById('methodology-reviewed');
  if (r) r.textContent = data.last_updated;
}

function renderClusterMetrics(h) {
  var el = document.getElementById('cluster-metrics');
  if (!el) return;
  var stats = [
    { l: 'Ship cases', v: h.total_cases },
    { l: 'Ship deaths', v: h.total_deaths },
    { l: 'Ship CFR', v: h.cfr_percent + '%' },
    { l: 'Attack rate', v: h.attack_rate_percent + '%' },
    { l: 'R₀ estimate', v: h.r0_estimate },
    { l: 'Status', v: 'Quarantined' }
  ];
  el.innerHTML = stats.map(function(s) {
    return '<div class="metric"><span class="metric-val">' + s.v + '</span><span class="metric-lbl">' + s.l + '</span></div>';
  }).join('');
}

function outcomeInfo(outcome) {
  var lo = outcome.toLowerCase();
  if (lo.indexOf('deceased') !== -1) return { cls: 'outcome-deceased', sym: '✖' };
  if (lo.indexOf('hospitalized') !== -1) return { cls: 'outcome-hospitalized', sym: '●' };
  if (lo.indexOf('recovering') !== -1 || lo.indexOf('mild') !== -1) return { cls: 'outcome-recovering', sym: '✔' };
  return { cls: 'outcome-unknown', sym: '?' };
}

function renderCaseTable(h) {
  var tbody = document.getElementById('case-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  h.cases.forEach(function(c) {
    var oi = outcomeInfo(c.outcome);
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td>#' + c.id + '</td>' +
      '<td>' + c.date + '</td>' +
      '<td>' + c.nationality + '</td>' +
      '<td class="td-desc">' + c.description + '</td>' +
      '<td><span class="outcome-badge ' + oi.cls + '"><span class="outcome-sym">' + oi.sym + '</span> ' + c.outcome + '</span></td>';
    tbody.appendChild(tr);
  });
}

function renderCaseCards(h) {
  var el = document.getElementById('case-cards');
  if (!el) return;
  el.innerHTML = '';
  h.cases.forEach(function(c) {
    var oi = outcomeInfo(c.outcome);
    var div = document.createElement('div');
    div.className = 'case-card-item';
    div.innerHTML =
      '<div class="case-card-header"><span class="case-card-id">Case #' + c.id + '</span><span class="case-card-date">' + c.date + '</span></div>' +
      '<div class="case-card-nation">' + c.nationality + '</div>' +
      '<div class="case-card-desc">' + c.description + '</div>' +
      '<span class="outcome-badge ' + oi.cls + '"><span class="outcome-sym">' + oi.sym + '</span> ' + c.outcome + '</span>';
    el.appendChild(div);
  });
}

function renderRoutePanel(h) {
  var ul = document.getElementById('route-timeline');
  if (!ul) return;
  ul.innerHTML = '';
  h.track.forEach(function(s) {
    var ev = s.label.toLowerCase().indexOf('case') !== -1 || s.label.toLowerCase().indexOf('quarantine') !== -1 || s.label.toLowerCase().indexOf('evacuation') !== -1;
    var li = document.createElement('li');
    li.className = 'route-stop' + (ev ? ' event' : '');
    li.innerHTML = '<span class="route-date">' + s.date.substring(5) + '</span> ' + s.label;
    ul.appendChild(li);
  });
}

// News
var officialSources = ['WHO', 'CDC', 'ECDC', 'RKI', 'PAHO', 'Africa CDC'];

function classifySev(a) {
  var t = (a.title + ' ' + a.summary).toLowerCase();
  if (t.indexOf('death') !== -1 || t.indexOf('fatali') !== -1 || t.indexOf('risk assessment') !== -1 || t.indexOf('level 3') !== -1) return 'alert';
  if (t.indexOf('advisory') !== -1 || t.indexOf('travel') !== -1 || t.indexOf('warning') !== -1) return 'advisory';
  if (t.indexOf('case') !== -1 || t.indexOf('update') !== -1 || t.indexOf('surveillance') !== -1 || t.indexOf('confirm') !== -1) return 'update';
  return 'background';
}

var sevLabels = { alert: 'Alert', advisory: 'Advisory', update: 'Update', background: 'Info' };
var allArticles = [];

function renderNewsFeed(data, filter) {
  allArticles = data.articles;
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
    var sev = classifySev(a);
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

function initFilterTabs(newsData) {
  var tabs = document.querySelectorAll('.filter-tab');
  tabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      tabs.forEach(function(t) { t.classList.remove('active'); });
      tab.classList.add('active');
      renderNewsFeed(newsData, tab.dataset.filter);
    });
  });
}

async function init() {
  var cases = await loadJSON('data/cases.json');
  var hondius = await loadJSON('data/hondius.json');
  var historical = await loadJSON('data/historical.json');
  var news = await loadJSON('data/news.json');

  renderMeta(cases);
  renderHeroStats(cases, hondius);
  renderStatGrid(cases);
  renderClusterMetrics(hondius);
  renderCaseTable(hondius);
  renderCaseCards(hondius);
  renderRoutePanel(hondius);
  renderNewsFeed(news, 'all');
  initFilterTabs(news);
  initMap(cases, hondius);
  initCharts(cases, historical);
}

document.addEventListener('DOMContentLoaded', init);
