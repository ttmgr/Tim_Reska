var blue = '#2563eb';
var red = '#dc2626';
var grey = '#94a3b8';
var gridColor = '#e2e8f0';
var amber = '#d97706';

var eventAnnotations = {
  annotations: {
    a1: {
      type: 'line', scaleID: 'x',
      value: new Date('2026-04-12').getTime(),
      borderColor: grey, borderWidth: 1, borderDash: [4, 4],
      label: { display: true, content: 'First case · Apr 12', position: 'start', yAdjust: -12,
        font: { size: 10, family: 'Inter' }, color: grey, backgroundColor: 'rgba(255,255,255,0.85)', padding: 3 }
    },
    a2: {
      type: 'line', scaleID: 'x',
      value: new Date('2026-04-18').getTime(),
      borderColor: red, borderWidth: 1, borderDash: [4, 4],
      label: { display: true, content: 'First death · Apr 18', position: 'start', yAdjust: -12,
        font: { size: 10, family: 'Inter' }, color: red, backgroundColor: 'rgba(255,255,255,0.85)', padding: 3 }
    },
    a3: {
      type: 'line', scaleID: 'x',
      value: new Date('2026-05-01').getTime(),
      borderColor: amber, borderWidth: 1, borderDash: [4, 4],
      label: { display: true, content: 'Quarantined · May 1', position: 'start', yAdjust: -12,
        font: { size: 10, family: 'Inter' }, color: amber, backgroundColor: 'rgba(255,255,255,0.85)', padding: 3 }
    }
  }
};

var legendCfg = { position: 'bottom', labels: { font: { family: 'Inter', size: 12 }, boxWidth: 12, padding: 16 } };

function timeXScale(unit) {
  return {
    type: 'time',
    time: { unit: unit || 'month', displayFormats: { month: 'MMM', week: 'MMM d', day: 'MMM d' }, tooltipFormat: 'MMM d, yyyy' },
    ticks: { font: { family: 'Inter', size: 12 }, maxTicksLimit: 7 },
    grid: { display: false }
  };
}

var yScaleCfg = { beginAtZero: true, ticks: { font: { family: 'Inter', size: 12 } }, grid: { color: gridColor } };

function initCharts(cases, historical) {
  epiCurve(cases);
  cumulative(cases);
  regional(cases);

  var hist = document.getElementById('ref-historical');
  if (hist) {
    var done = false;
    new MutationObserver(function() {
      if (hist.classList.contains('open') && !done) {
        done = true;
        histEU(historical);
        histUS(historical);
      }
    }).observe(hist, { attributes: true, attributeFilter: ['class'] });
  }
}

function weeklyNew(tl) {
  var w = [];
  for (var i = 1; i < tl.length; i++) {
    w.push({
      x: new Date(tl[i].date),
      nc: tl[i].cumulative_cases - tl[i - 1].cumulative_cases,
      nd: tl[i].cumulative_deaths - tl[i - 1].cumulative_deaths
    });
  }
  return w;
}

function epiCurve(cases) {
  var el = document.getElementById('chart-epicurve');
  if (!el) return;
  var w = weeklyNew(cases.timeline);

  new Chart(el.getContext('2d'), {
    type: 'bar',
    data: {
      datasets: [
        { label: 'New cases', data: w.map(function(d) { return { x: d.x, y: d.nc }; }), backgroundColor: blue + '60', borderColor: blue, borderWidth: 1 },
        { label: 'New deaths', data: w.map(function(d) { return { x: d.x, y: d.nd }; }), backgroundColor: red + '60', borderColor: red, borderWidth: 1 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: legendCfg, annotation: eventAnnotations },
      scales: {
        x: timeXScale('month'),
        y: Object.assign({}, yScaleCfg, { title: { display: true, text: 'Cases per period', font: { family: 'Inter', size: 12 } } })
      }
    }
  });
}

function cumulative(cases) {
  var el = document.getElementById('chart-timeline');
  if (!el) return;
  var data = cases.timeline.map(function(d) { return { x: new Date(d.date), y: d.cumulative_cases }; });
  var deaths = cases.timeline.map(function(d) { return { x: new Date(d.date), y: d.cumulative_deaths }; });

  new Chart(el.getContext('2d'), {
    type: 'line',
    data: {
      datasets: [
        { label: 'Cumulative cases (global)', data: data, borderColor: blue, backgroundColor: blue + '1a', fill: true, tension: 0.3, pointRadius: 3, borderWidth: 2 },
        { label: 'Cumulative deaths (global)', data: deaths, borderColor: red, backgroundColor: red + '1a', fill: true, tension: 0.3, pointRadius: 3, borderWidth: 2 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: legendCfg, annotation: eventAnnotations },
      scales: { x: timeXScale('month'), y: yScaleCfg }
    }
  });
}

function regional(cases) {
  var el = document.getElementById('chart-regional');
  if (!el) return;

  var nonAR = cases.countries
    .filter(function(c) { return c.cases_2026 > 0 && c.iso !== 'AR'; })
    .sort(function(a, b) { return b.cases_2026 - a.cases_2026; });

  var arData = cases.countries.find(function(c) { return c.iso === 'AR'; });

  var arNote = document.getElementById('argentina-note');
  if (arNote && arData) {
    arNote.textContent = 'Argentina: ' + arData.cases_2026 + ' cases (excluded from chart for scale clarity)';
    arNote.style.display = '';
  }

  new Chart(el.getContext('2d'), {
    type: 'bar',
    data: {
      labels: nonAR.map(function(c) { return c.name; }),
      datasets: [
        { label: 'Cases', data: nonAR.map(function(c) { return c.cases_2026; }), backgroundColor: blue + '40', borderColor: blue, borderWidth: 1 },
        { label: 'Deaths', data: nonAR.map(function(c) { return c.deaths_2026; }), backgroundColor: red + '40', borderColor: red, borderWidth: 1 }
      ]
    },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: legendCfg },
      scales: {
        x: { beginAtZero: true, ticks: { font: { family: 'Inter', size: 12 } }, grid: { color: gridColor } },
        y: { ticks: { font: { family: 'Inter', size: 12 } }, grid: { display: false } }
      }
    }
  });
}

function trend(data) {
  var n = data.length, sx = 0, sy = 0, sxy = 0, sxx = 0;
  for (var i = 0; i < n; i++) { sx += i; sy += data[i]; sxy += i * data[i]; sxx += i * i; }
  var m = (n * sxy - sx * sy) / (n * sxx - sx * sx), b = (sy - m * sx) / n;
  return data.map(function(_, i) { return Math.round(b + m * i); });
}

function histEU(h) {
  var el = document.getElementById('chart-historical-eu');
  if (!el) return;
  var eu = h.eu_ecdc.annual, de = h.de_rki.annual;
  var euC = eu.map(function(d) { return d.cases; });
  new Chart(el.getContext('2d'), {
    type: 'bar',
    data: {
      labels: eu.map(function(d) { return d.year; }),
      datasets: [
        { label: 'EU/EEA', data: euC, backgroundColor: blue + '30', borderColor: blue, borderWidth: 1 },
        { label: 'Germany', data: de.map(function(d) { return d.cases; }), backgroundColor: grey + '30', borderColor: grey, borderWidth: 1 },
        { label: 'Trend', data: trend(euC), type: 'line', borderColor: grey, borderWidth: 1.5, borderDash: [4, 4], pointRadius: 0, fill: false }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: legendCfg }, scales: { x: { ticks: { font: { family: 'Inter', size: 12 } }, grid: { display: false } }, y: yScaleCfg } }
  });
}

function histUS(h) {
  var el = document.getElementById('chart-historical-us');
  if (!el) return;
  var us = h.us_cdc.annual;
  new Chart(el.getContext('2d'), {
    type: 'bar',
    data: {
      labels: us.map(function(d) { return d.year; }),
      datasets: [{ label: 'US (CDC)', data: us.map(function(d) { return d.cases; }), backgroundColor: blue + '30', borderColor: blue, borderWidth: 1 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: legendCfg }, scales: { x: { ticks: { font: { family: 'Inter', size: 12 } }, grid: { display: false } }, y: yScaleCfg } }
  });
}
