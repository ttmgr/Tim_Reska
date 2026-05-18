async function loadJSON(p) { return (await fetch(p)).json(); }

function renderHeroStats(data) {
  var s = data.summary;
  var chips = [
    { val: s.total_confirmed, label: 'Confirmed', sub: 'Lab-confirmed (Bundibugyo RT-PCR)', cls: 'blue', subCls: '' },
    { val: s.total_suspected, label: 'Suspected', sub: 'Pending confirmation', cls: 'default', subCls: '' },
    { val: s.total_deaths_all, label: 'Deaths', sub: s.deaths_confirmed + ' confirmed + ' + s.deaths_suspected + ' suspected', cls: 'red', subCls: '' },
    { val: 'PHEIC', label: 'WHO status', sub: 'Declared ' + s.pheic_date, cls: 'red', subCls: '' }
  ];
  var el = document.getElementById('hero-stats');
  if (!el) return;
  el.innerHTML = chips.map(function(c) {
    return '<div class="stat-chip ' + c.cls + '">' +
      '<span class="stat-value">' + (typeof c.val === 'number' ? c.val.toLocaleString() : c.val) + '</span>' +
      '<span class="stat-label">' + c.label + '</span>' +
      (c.sub ? '<span class="stat-sub ' + c.subCls + '">' + c.sub + '</span>' : '') +
      '</div>';
  }).join('');
}

function renderStatGrid(data) {
  var s = data.summary;
  var d = s.weekly_delta || {};
  var cards = [
    { val: s.total_confirmed, label: 'Confirmed cases', sub: 'Bundibugyo-specific RT-PCR', delta: d.confirmed, type: 'cases', cls: 'blue-top' },
    { val: s.total_suspected, label: 'Suspected cases', sub: 'Clinical + epi link', delta: d.suspected, type: 'cases', cls: 'amber-top' },
    { val: s.total_deaths_all, label: 'Total deaths', sub: 'Confirmed + suspected', delta: d.deaths, type: 'deaths', cls: 'red-top' },
    { val: s.countries_affected, label: 'Countries affected', sub: 'DRC + Uganda', delta: null, cls: '' }
  ];
  var el = document.getElementById('stat-grid');
  if (!el) return;
  el.innerHTML = cards.map(function(c) {
    var deltaHtml = '';
    if (c.delta !== null && c.delta !== undefined) {
      if (c.delta === 0) deltaHtml = '<div class="delta delta-flat">No change this week</div>';
      else {
        var cls = c.delta > 0 ? 'delta-up' : 'delta-down';
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

function renderOutbreakMetrics(outbreak) {
  var el = document.getElementById('outbreak-metrics');
  if (!el) return;
  var k = outbreak.key_metrics;
  var stats = [
    { l: 'HCW deaths', v: k.hcw_deaths },
    { l: 'HCW cases', v: k.hcw_cases },
    { l: 'Sample positivity', v: k.sample_positivity },
    { l: 'Historical CFR', v: outbreak.historical_cfr_percent + '%' },
    { l: 'Diagnostic delay', v: k.diagnostic_delay_days + ' days' },
    { l: 'DRC outbreak #', v: outbreak.drc_outbreak_number }
  ];
  el.innerHTML = stats.map(function(s) {
    return '<div class="metric"><span class="metric-val">' + s.v + '</span><span class="metric-lbl">' + s.l + '</span></div>';
  }).join('');
}

function outcomeInfo(outcome) {
  var lo = outcome.toLowerCase();
  if (lo.indexOf('deceased') !== -1) return { cls: 'outcome-deceased', sym: '✖' };
  if (lo.indexOf('treatment') !== -1 || lo.indexOf('hospitalized') !== -1) return { cls: 'outcome-hospitalized', sym: '●' };
  if (lo.indexOf('recovering') !== -1) return { cls: 'outcome-recovering', sym: '✔' };
  return { cls: 'outcome-unknown', sym: '?' };
}

function renderCaseTable(outbreak) {
  var tbody = document.getElementById('case-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  outbreak.confirmed_cases.forEach(function(c) {
    var oi = outcomeInfo(c.outcome);
    var hcwBadge = c.hcw ? ' <span class="pill pill-amber" style="font-size:10px;padding:2px 6px">HCW</span>' : '';
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td>#' + c.id + hcwBadge + '</td>' +
      '<td>' + c.date + '</td>' +
      '<td>' + c.region + '</td>' +
      '<td class="td-desc">' + c.description + '</td>' +
      '<td><span class="outcome-badge ' + oi.cls + '"><span class="outcome-sym">' + oi.sym + '</span> ' + c.outcome + '</span></td>';
    tbody.appendChild(tr);
  });
}

function renderCaseCards(outbreak) {
  var el = document.getElementById('case-cards');
  if (!el) return;
  el.innerHTML = '';
  outbreak.confirmed_cases.forEach(function(c) {
    var oi = outcomeInfo(c.outcome);
    var hcwBadge = c.hcw ? ' <span class="pill pill-amber" style="font-size:10px;padding:2px 6px">HCW</span>' : '';
    var div = document.createElement('div');
    div.className = 'case-card-item';
    div.innerHTML =
      '<div class="case-card-header"><span class="case-card-id">Case #' + c.id + hcwBadge + '</span><span class="case-card-date">' + c.date + '</span></div>' +
      '<div class="case-card-nation">' + c.region + '</div>' +
      '<div class="case-card-desc">' + c.description + '</div>' +
      '<span class="outcome-badge ' + oi.cls + '"><span class="outcome-sym">' + oi.sym + '</span> ' + c.outcome + '</span>';
    el.appendChild(div);
  });
}

function renderResponseTimeline(outbreak) {
  var ul = document.getElementById('response-timeline');
  if (!ul) return;
  ul.innerHTML = '';
  outbreak.response_timeline.forEach(function(s) {
    var ev = s.severity === 'pheic' || s.severity === 'alert' || s.severity === 'death';
    var li = document.createElement('li');
    li.className = 'route-stop' + (ev ? ' event' : '');
    li.innerHTML = '<span class="route-date">' + s.date.substring(5) + '</span> ' + s.event;
    ul.appendChild(li);
  });
}

var officialSources = ['WHO', 'CDC', 'ECDC', 'Africa CDC', 'INRB'];

function classifySev(a) {
  var t = (a.title + ' ' + a.summary).toLowerCase();
  if (t.indexOf('pheic') !== -1 || t.indexOf('emergency') !== -1 || t.indexOf('death') !== -1 || t.indexOf('fatali') !== -1) return 'alert';
  if (t.indexOf('advisory') !== -1 || t.indexOf('travel') !== -1 || t.indexOf('warning') !== -1 || t.indexOf('lethality') !== -1) return 'advisory';
  if (t.indexOf('case') !== -1 || t.indexOf('update') !== -1 || t.indexOf('confirm') !== -1 || t.indexOf('mobilize') !== -1) return 'update';
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
  var outbreak = await loadJSON('data/outbreak.json');
  var historical = await loadJSON('data/historical.json');
  var news = await loadJSON('data/news.json');

  renderMeta(cases);
  renderHeroStats(cases);
  renderStatGrid(cases);
  renderOutbreakMetrics(outbreak);
  renderCaseTable(outbreak);
  renderCaseCards(outbreak);
  renderResponseTimeline(outbreak);
  renderNewsFeed(news, 'all');
  initFilterTabs(news);
  initMap(cases);
  initCharts(cases, historical);
}

document.addEventListener('DOMContentLoaded', init);
