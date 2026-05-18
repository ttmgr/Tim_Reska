var blue = '#2563eb';
var red = '#dc2626';
var amber = '#d97706';
var grey = '#94a3b8';
var gridColor = '#E8E6E1';

var eventAnnotations = {
  annotations: {
    a1: {
      type: 'line', scaleID: 'x',
      value: new Date('2026-04-24').getTime(),
      borderColor: grey, borderWidth: 1, borderDash: [4, 4],
      label: { display: true, content: 'First case · Apr 24', position: 'start', yAdjust: -12,
        font: { size: 10, family: 'Inter' }, color: grey, backgroundColor: 'rgba(255,255,255,0.85)', padding: 3 }
    },
    a2: {
      type: 'line', scaleID: 'x',
      value: new Date('2026-05-14').getTime(),
      borderColor: amber, borderWidth: 1, borderDash: [4, 4],
      label: { display: true, content: 'Lab confirmed · May 14', position: 'start', yAdjust: -12,
        font: { size: 10, family: 'Inter' }, color: amber, backgroundColor: 'rgba(255,255,255,0.85)', padding: 3 }
    },
    a3: {
      type: 'line', scaleID: 'x',
      value: new Date('2026-05-17').getTime(),
      borderColor: red, borderWidth: 1, borderDash: [4, 4],
      label: { display: true, content: 'PHEIC · May 17', position: 'start', yAdjust: -12,
        font: { size: 10, family: 'Inter' }, color: red, backgroundColor: 'rgba(255,255,255,0.85)', padding: 3 }
    }
  }
};

var legendCfg = { position: 'bottom', labels: { font: { family: 'Inter', size: 12 }, boxWidth: 12, padding: 16 } };

function timeXScale(unit) {
  return {
    type: 'time',
    time: { unit: unit || 'day', displayFormats: { day: 'MMM d', week: 'MMM d' }, tooltipFormat: 'MMM d, yyyy' },
    ticks: { font: { family: 'Inter', size: 12 }, maxTicksLimit: 8 },
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
        histDRC(historical);
      }
    }).observe(hist, { attributes: true, attributeFilter: ['class'] });
  }
}

function periodNew(tl) {
  var w = [];
  for (var i = 1; i < tl.length; i++) {
    w.push({
      x: new Date(tl[i].date),
      nc: tl[i].confirmed - tl[i - 1].confirmed,
      ns: tl[i].suspected - tl[i - 1].suspected,
      nd: tl[i].deaths - tl[i - 1].deaths
    });
  }
  return w;
}

function epiCurve(cases) {
  var el = document.getElementById('chart-epicurve');
  if (!el) return;
  var w = periodNew(cases.timeline);

  new Chart(el.getContext('2d'), {
    type: 'bar',
    data: {
      datasets: [
        { label: 'New suspected', data: w.map(function(d) { return { x: d.x, y: d.ns }; }), backgroundColor: amber + '50', borderColor: amber, borderWidth: 1 },
        { label: 'New confirmed', data: w.map(function(d) { return { x: d.x, y: d.nc }; }), backgroundColor: blue + '60', borderColor: blue, borderWidth: 1 },
        { label: 'New deaths', data: w.map(function(d) { return { x: d.x, y: d.nd }; }), backgroundColor: red + '50', borderColor: red, borderWidth: 1 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: legendCfg, annotation: eventAnnotations },
      scales: {
        x: timeXScale('day'),
        y: Object.assign({}, yScaleCfg, { title: { display: true, text: 'Cases per period', font: { family: 'Inter', size: 12 } } })
      }
    }
  });
}

function cumulative(cases) {
  var el = document.getElementById('chart-cumulative');
  if (!el) return;
  var suspected = cases.timeline.map(function(d) { return { x: new Date(d.date), y: d.suspected }; });
  var confirmed = cases.timeline.map(function(d) { return { x: new Date(d.date), y: d.confirmed }; });
  var deaths = cases.timeline.map(function(d) { return { x: new Date(d.date), y: d.deaths }; });

  new Chart(el.getContext('2d'), {
    type: 'line',
    data: {
      datasets: [
        { label: 'Cumulative suspected', data: suspected, borderColor: amber, backgroundColor: amber + '1a', fill: true, tension: 0.3, pointRadius: 3, borderWidth: 2 },
        { label: 'Cumulative confirmed', data: confirmed, borderColor: blue, backgroundColor: blue + '1a', fill: true, tension: 0.3, pointRadius: 3, borderWidth: 2 },
        { label: 'Cumulative deaths', data: deaths, borderColor: red, backgroundColor: red + '1a', fill: true, tension: 0.3, pointRadius: 3, borderWidth: 2 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: legendCfg, annotation: eventAnnotations },
      scales: { x: timeXScale('day'), y: yScaleCfg }
    }
  });
}

function regional(cases) {
  var el = document.getElementById('chart-regional');
  if (!el) return;

  var regions = cases.regions.sort(function(a, b) {
    return (b.confirmed + b.suspected) - (a.confirmed + a.suspected);
  });

  new Chart(el.getContext('2d'), {
    type: 'bar',
    data: {
      labels: regions.map(function(r) { return r.name; }),
      datasets: [
        { label: 'Confirmed', data: regions.map(function(r) { return r.confirmed; }), backgroundColor: blue + '60', borderColor: blue, borderWidth: 1 },
        { label: 'Suspected', data: regions.map(function(r) { return r.suspected; }), backgroundColor: amber + '40', borderColor: amber, borderWidth: 1 },
        { label: 'Deaths', data: regions.map(function(r) { return r.deaths_confirmed + r.deaths_suspected; }), backgroundColor: red + '40', borderColor: red, borderWidth: 1 }
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

function histDRC(h) {
  var el = document.getElementById('chart-historical');
  if (!el) return;
  var data = h.drc_outbreaks;

  var bgColors = data.map(function(d) {
    return d.virus === 'Bundibugyo' ? amber + '60' : blue + '30';
  });
  var borderColors = data.map(function(d) {
    return d.virus === 'Bundibugyo' ? amber : blue;
  });

  new Chart(el.getContext('2d'), {
    type: 'bar',
    data: {
      labels: data.map(function(d) { return d.year + ' ' + d.province.substring(0, 8); }),
      datasets: [
        { label: 'Cases', data: data.map(function(d) { return d.cases; }), backgroundColor: bgColors, borderColor: borderColors, borderWidth: 1 },
        { label: 'Deaths', data: data.map(function(d) { return d.deaths; }), backgroundColor: red + '30', borderColor: red, borderWidth: 1 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: legendCfg,
        tooltip: {
          callbacks: {
            title: function(items) {
              var i = items[0].dataIndex;
              return data[i].year + ' — ' + data[i].province + ' (' + data[i].virus + ')';
            }
          }
        }
      },
      scales: {
        x: { ticks: { font: { family: 'Inter', size: 10 }, maxRotation: 60, minRotation: 40 }, grid: { display: false } },
        y: yScaleCfg
      }
    }
  });
}
