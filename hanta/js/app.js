function renderHeroStats(data, hondius) {
  var h = hondius || {};
  renderStatChips('hero-stats', [
    { val: h.total_cases || '--', label: 'Ship cases', sub: 'MV Hondius cluster', cls: 'blue' },
    { val: h.total_deaths || '--', label: 'Ship deaths', sub: 'All passengers aged 57-68', cls: 'red' },
    { val: (h.cfr_percent || '--') + '%', label: 'Ship CFR', sub: 'Case fatality rate', cls: 'red' },
    { val: 'Quarantined', label: 'Status', sub: 'En route Tenerife', cls: 'default' }
  ]);
}

function renderStatGrid(data) {
  var s = data.summary;
  var d = s.weekly_delta || {};
  renderDeltaStatCards('stat-grid', [
    { val: s.total_cases_2026, label: 'Global total cases', sub: 'All 2026 reported cases worldwide', delta: d.cases, cls: 'blue-top' },
    { val: s.total_deaths_2026, label: 'Global total deaths', sub: 'Global CFR: ' + s.cfr_percent + '%', delta: d.deaths, cls: 'red-top', zeroLabel: 'No new deaths this week' },
    { val: s.countries_affected, label: 'Countries affected', sub: 'Cases or contact tracing', delta: null, cls: '' },
    { val: s.active_clusters, label: 'Active clusters', sub: 'MV Hondius (ANDV)', delta: null, cls: 'amber-top' }
  ]);
}

function renderClusterMetrics(h) {
  renderMetricGrid('cluster-metrics', [
    { l: 'Ship cases', v: h.total_cases },
    { l: 'Ship deaths', v: h.total_deaths },
    { l: 'Ship CFR', v: h.cfr_percent + '%' },
    { l: 'Attack rate', v: h.attack_rate_percent + '%' },
    { l: 'R₀ estimate', v: h.r0_estimate },
    { l: 'Status', v: 'Quarantined' }
  ]);
}

var OUTCOME_MAP = {
  keywords: [
    { match: ['deceased'], cls: 'outcome-deceased', sym: '✖' },
    { match: ['hospitalized'], cls: 'outcome-hospitalized', sym: '●' },
    { match: ['recovering', 'mild'], cls: 'outcome-recovering', sym: '✔' }
  ],
  unknown: { cls: 'outcome-unknown', sym: '?' }
};
function outcomeInfo(outcome) { return classifyOutcome(outcome, OUTCOME_MAP); }

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
  renderNewsFeed(news, 'all', classifySev, officialSources);
  initFilterTabs(news, classifySev, officialSources);
  initMap(cases, hondius);
  initCharts(cases, historical);
}

document.addEventListener('DOMContentLoaded', init);
