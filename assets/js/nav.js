(function () {
  var scripts = document.querySelectorAll('script[src*="nav.js"]');
  var scriptSrc = scripts.length ? scripts[scripts.length - 1].getAttribute('src') : '';
  var depth = scriptSrc.replace(/assets\/js\/nav\.js.*$/, '');

  // Manifest is loaded synchronously via assets/js/nav-manifest.js (declares
  // window.TR_NAV_LINKS). Bail quietly if the page forgot to include it.
  var links = window.TR_NAV_LINKS;
  if (!links || !links.length) return;

  var css = [
    '.tr-nav{position:fixed;top:0;left:0;right:0;z-index:9999;',
    'background:rgba(250,249,247,0.88);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);',
    'border-bottom:1px solid #E8E6E1;font-family:"Inter",-apple-system,sans-serif}',
    '.tr-nav-inner{display:flex;align-items:center;justify-content:space-between;',
    'max-width:1140px;margin:0 auto;padding:0 24px;height:52px}',
    '.tr-nav a{color:#6B6A73;text-decoration:none;font-size:13px;font-weight:500;transition:color .2s}',
    '.tr-nav a:hover{color:#1A1A2E}',
    '.tr-nav-brand{font-family:"Source Serif 4",Georgia,serif;font-size:16px;font-weight:600;color:#1A1A2E!important}',
    '.tr-nav-links{display:flex;gap:24px;list-style:none;margin:0;padding:0}',
    '.tr-nav-back{display:inline-flex;align-items:center;gap:6px;padding:6px 16px;',
    'border:1px solid #E8E6E1;border-radius:8px;font-size:13px;font-weight:500;transition:all .2s}',
    '.tr-nav-back:hover{border-color:#C4794A;color:#C4794A!important}',
    '@media(max-width:640px){.tr-nav-links{display:none}.tr-nav-back{font-size:12px;padding:5px 12px}}'
  ].join('\n');

  // Current-page detection: slug match in pathname. Robust against renames of
  // the human-readable label, which the old substring-on-label check wasn't.
  var currentPath = window.location.pathname;
  var linkHTML = links
    .filter(function (l) { return currentPath.indexOf('/' + l.slug + '/') === -1; })
    .slice(0, 4)
    .map(function (l) { return '<li><a href="' + depth + l.path + '">' + l.label + '</a></li>'; })
    .join('');

  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  var nav = document.createElement('nav');
  nav.className = 'tr-nav';
  nav.setAttribute('aria-label', 'Portfolio navigation');
  nav.innerHTML = '<div class="tr-nav-inner">' +
    '<a href="' + depth + '" class="tr-nav-brand">Tim Reska</a>' +
    '<ul class="tr-nav-links">' + linkHTML + '</ul>' +
    '<a href="' + depth + '" class="tr-nav-back">&larr; Portfolio</a>' +
    '</div>';
  document.body.prepend(nav);

  document.body.style.paddingTop = '52px';
})();
