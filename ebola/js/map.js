var mapInstance = null;
var defaultBounds = [[-5, 25], [8, 35]];

function initMap(cases) {
  mapInstance = L.map('map', {
    scrollWheelZoom: false,
    zoomControl: true,
    tap: false,
    dragging: !L.Browser.mobile,
    touchZoom: true,
    maxBounds: [[-10, 15], [15, 45]],
    maxBoundsViscosity: 1.0
  });

  mapInstance.fitBounds(defaultBounds, { padding: [20, 20], maxZoom: 7 });

  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(mapInstance);

  var red = '#dc2626';
  var amber = '#d97706';
  var gray = '#64748b';

  cases.regions.forEach(function(r) {
    var hasDeaths = r.deaths_confirmed > 0;
    var total = r.confirmed + r.suspected;
    var radius = Math.max(8, Math.sqrt(total) * 3);
    var color = hasDeaths ? red : amber;

    var marker = L.circleMarker([r.lat, r.lon], {
      radius: radius, fillColor: color, color: color,
      weight: 2, opacity: 0.9, fillOpacity: 0.3
    }).addTo(mapInstance);

    var popup = '<strong style="font-size:14px">' + r.name + '</strong>';
    if (r.province) popup += '<br><span style="color:#6B6A73;font-size:12px">' + r.province + ', ' + r.country + '</span>';
    popup += '<br>Confirmed: <span class="popup-cases">' + r.confirmed + '</span>';
    popup += '&ensp;Suspected: <strong>' + r.suspected + '</strong>';
    if (hasDeaths) popup += '<br>Deaths: <span class="popup-deaths">' + (r.deaths_confirmed + r.deaths_suspected) + '</span>';
    popup += '<br><span style="color:#6B6A73;font-size:11px">' + r.role + '</span>';
    if (r.notes) popup += '<br><span style="color:#9B9A94;font-size:11px">' + r.notes + '</span>';

    marker.bindPopup(popup, { maxWidth: 280 });
    marker.on('mouseover', function() { this.openPopup(); });
    marker.on('mouseout', function() { this.closePopup(); });

    var label = L.divIcon({
      className: '',
      html: '<span style="font-family:Inter,system-ui,sans-serif;font-size:11px;font-weight:700;color:' + color + '">' + r.name.split(' ')[0] + '</span>',
      iconSize: [60, 14], iconAnchor: [-8, 7]
    });
    L.marker([r.lat, r.lon], { icon: label, interactive: false }).addTo(mapInstance);
  });

  if (cases.at_risk) {
    cases.at_risk.forEach(function(c) {
      var marker = L.circleMarker([c.lat, c.lon], {
        radius: 6, fillColor: gray, color: gray,
        weight: 1.5, opacity: 0.7, fillOpacity: 0.15
      }).addTo(mapInstance);

      marker.bindPopup(
        '<strong>' + c.name + '</strong><br>' +
        '<span style="color:#6B6A73">' + c.status + '</span>' +
        (c.notes ? '<br><span style="color:#9B9A94;font-size:11px">' + c.notes + '</span>' : ''),
        { maxWidth: 240 }
      );
      marker.on('mouseover', function() { this.openPopup(); });
      marker.on('mouseout', function() { this.closePopup(); });
    });
  }

  var resetBtn = document.getElementById('map-reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', function() {
      mapInstance.fitBounds(defaultBounds, { padding: [20, 20], maxZoom: 7 });
    });
  }
}
