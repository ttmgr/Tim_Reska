function renderHeroStats(data) {
  var s = data.summary;
  renderStatChips('hero-stats', [
    { val: s.total_confirmed, label: 'Confirmed', sub: 'Lab-confirmed (Bundibugyo RT-PCR)', cls: 'blue' },
    { val: s.total_suspected, label: 'Suspected', sub: 'Pending confirmation', cls: 'default' },
    { val: s.total_deaths_all, label: 'Deaths', sub: s.deaths_confirmed + ' confirmed + ' + s.deaths_suspected + ' suspected', cls: 'red' },
    { val: 'PHEIC', label: 'WHO status', sub: 'Declared ' + s.pheic_date, cls: 'red' }
  ]);
}

function renderStatGrid(data) {
  var s = data.summary;
  var d = s.weekly_delta || {};
  renderDeltaStatCards('stat-grid', [
    { val: s.total_confirmed, label: 'Confirmed cases', sub: 'Bundibugyo-specific RT-PCR', delta: d.confirmed, cls: 'blue-top', zeroLabel: 'No change this week' },
    { val: s.total_suspected, label: 'Suspected cases', sub: 'Clinical + epi link', delta: d.suspected, cls: 'amber-top', zeroLabel: 'No change this week' },
    { val: s.total_deaths_all, label: 'Total deaths', sub: 'Confirmed + suspected', delta: d.deaths, cls: 'red-top', zeroLabel: 'No change this week' },
    { val: s.countries_affected, label: 'Countries affected', sub: 'DRC + Uganda', delta: null, cls: '' }
  ]);
}

function renderOutbreakMetrics(outbreak) {
  var k = outbreak.key_metrics;
  renderMetricGrid('outbreak-metrics', [
    { l: 'HCW deaths', v: k.hcw_deaths },
    { l: 'HCW cases', v: k.hcw_cases },
    { l: 'Sample positivity', v: k.sample_positivity },
    { l: 'Historical CFR', v: outbreak.historical_cfr_percent + '%' },
    { l: 'Diagnostic delay', v: k.diagnostic_delay_days + ' days' },
    { l: 'DRC outbreak #', v: outbreak.drc_outbreak_number }
  ]);
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
  renderNewsFeed(news, 'all', classifySev, officialSources);
  initFilterTabs(news, classifySev, officialSources);
  initMap(cases);
  initCharts(cases, historical);
}

document.addEventListener('DOMContentLoaded', init);
