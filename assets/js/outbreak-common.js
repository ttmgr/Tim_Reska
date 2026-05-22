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
