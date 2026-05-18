var mapInstance = null;
var defaultBounds = [[-55, -75], [55, 20]];

function initMap(cases, hondius) {
  mapInstance = L.map('map', {
    scrollWheelZoom: false,
    zoomControl: true,
    tap: false,
    dragging: !L.Browser.mobile,
    touchZoom: true,
    maxBounds: [[-70, -120], [70, 60]],
    maxBoundsViscosity: 1.0
  });

  mapInstance.fitBounds(defaultBounds, { padding: [20, 20], maxZoom: 4 });

  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(mapInstance);

  var blue = '#2563eb';
  var red = '#dc2626';
  var gray = '#64748b';

  cases.countries.forEach(function(c) {
    var has = c.cases_2026 > 0;
    var dead = c.deaths_2026 > 0;
    var mon = c.risk_level === 'MONITORING';
    if (!has && !mon) return;

    var r = has ? Math.max(8, Math.sqrt(c.cases_2026) * 5) : 6;
    var color = dead ? red : mon ? gray : blue;

    var marker = L.circleMarker([c.lat, c.lon], {
      radius: r, fillColor: color, color: color,
      weight: 2, opacity: 0.9, fillOpacity: has ? 0.3 : 0.15
    }).addTo(mapInstance);

    var popup = '<strong style="font-size:14px">' + c.name + '</strong>';
    if (has) popup += '<br>Cases: <span class="popup-cases">' + c.cases_2026 + '</span>';
    if (dead) popup += '&ensp;Deaths: <span class="popup-deaths">' + c.deaths_2026 + '</span>';
    if (c.cfr_percent > 0 && c.cases_2026 >= 2) popup += '<br>CFR: ' + c.cfr_percent + '%';
    if (c.notes) popup += '<br><span style="color:#64748b;font-size:11px">' + c.notes + '</span>';

    marker.bindPopup(popup, { maxWidth: 260 });
    marker.on('mouseover', function() { this.openPopup(); });
    marker.on('mouseout', function() { this.closePopup(); });

    if (c.cases_2026 >= 10) {
      var label = L.divIcon({
        className: '',
        html: '<span style="font-family:Inter,system-ui,sans-serif;font-size:11px;font-weight:700;color:' + color + '">' + c.cases_2026 + '</span>',
        iconSize: [30, 14], iconAnchor: [-8, 7]
      });
      L.marker([c.lat, c.lon], { icon: label, interactive: false }).addTo(mapInstance);
    }
  });

  var trackCoords = hondius.track.map(function(p) { return [p.lat, p.lon]; });

  L.polyline(trackCoords, {
    color: gray, weight: 2, dashArray: '8, 5', opacity: 0.6
  }).addTo(mapInstance);

  hondius.track.forEach(function(pt) {
    var isEvt = pt.label.toLowerCase().indexOf('case') !== -1 ||
                pt.label.toLowerCase().indexOf('quarantine') !== -1 ||
                pt.label.toLowerCase().indexOf('evacuation') !== -1;

    var m = L.circleMarker([pt.lat, pt.lon], {
      radius: isEvt ? 5 : 3,
      fillColor: isEvt ? red : gray,
      color: isEvt ? red : gray,
      weight: isEvt ? 1.5 : 1,
      fillOpacity: isEvt ? 0.7 : 0.4
    }).addTo(mapInstance);

    m.bindPopup('<strong>' + pt.label + '</strong><br><span style="color:#64748b">' + pt.date + '</span>', { maxWidth: 220 });
    m.on('mouseover', function() { this.openPopup(); });
    m.on('mouseout', function() { this.closePopup(); });
  });

  var resetBtn = document.getElementById('map-reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', function() {
      mapInstance.fitBounds(defaultBounds, { padding: [20, 20], maxZoom: 4 });
    });
  }
}
