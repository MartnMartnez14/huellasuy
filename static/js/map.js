export function createMaps(onPick) {
  if (!window.L) return null;
  const make = id => {
    const map = L.map(id).fitBounds([[-35.05, -58.45], [-30.05, -53.1]], {padding: [12, 12]});
    const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>', maxZoom: 19
    }).addTo(map);
    tiles.on('tileerror', () => {
      const message = document.getElementById(id === 'map' ? 'map-message' : 'location-message');
      message.textContent = 'No pudimos cargar algunas imágenes del mapa. Podés usar el listado o ingresar coordenadas manualmente.';
    });
    return map;
  };
  const map = make('map'), picker = make('picker'), layer = L.layerGroup().addTo(map);
  let chosen;
  const markers = new Map();
  function pick(lat, lon) {
    if (chosen) chosen.setLatLng([lat, lon]);
    else {
      chosen = L.marker([lat, lon], {draggable: true}).addTo(picker);
      chosen.on('dragend', () => { const p = chosen.getLatLng(); onPick(p.lat, p.lng); });
    }
    onPick(lat, lon);
  }
  picker.on('click', e => pick(e.latlng.lat, e.latlng.lng));
  return {map, picker, pick, focusReport(id) {
    const marker = markers.get(id);
    if (!marker) return false;
    map.invalidateSize();
    map.setView(marker.getLatLng(), 15);
    marker.openPopup();
    return true;
  }, render(reports, card) {
    const active = new Set(reports.map(r => r.id));
    for (const [id, marker] of markers) {
      if (!active.has(id)) { layer.removeLayer(marker); markers.delete(id); }
    }
    for (const r of reports) {
      let marker = markers.get(r.id);
      if (!marker) {
        const el = document.createElement('span'); el.className = 'pin';
        el.style.setProperty('--accent', r.pastel_color);
        el.textContent = r.animal_type === 'dog' ? '🐶' : r.animal_type === 'cat' ? '🐱' : '🐾';
        marker = L.marker([r.latitude, r.longitude], {icon: L.divIcon({html: el, className: '', iconSize: [34, 34]}), title: r.title})
          .bindPopup(() => card(r, false)).addTo(layer);
        markers.set(r.id, marker);
      } else {
        marker.setPopupContent(() => card(r, false));
      }
    }
  }};
}
