import {createMaps} from './map.js';
import {api, copy, remaining} from './reports.js';
const $ = id => document.getElementById(id);
const form = $('form'), dialog = $('report-dialog');
let reports = [], offset = 0, busy = false, online = false;
const focusedId = Number(location.pathname.match(/^\/(?:r|manage)\/(\d+)$/)?.[1]);
// Capture token before any UI interaction, then remove it from current history entry.
const privateToken = location.pathname.startsWith('/manage/') ? new URLSearchParams(location.hash.slice(1)).get('token') : null;
if (privateToken) history.replaceState(null, '', location.pathname);
const now = () => Date.now() + offset;
function locationPicked(lat, lon) {
  form.elements.latitude.value = lat.toFixed(3); form.elements.longitude.value = lon.toFixed(3);
  $('location-message').textContent = lat < -35.1 || lat > -30 || lon < -58.5 || lon > -53 ? 'Esta ubicación parece fuera de Uruguay. Revisala antes de publicar.' : 'Ubicación aproximada seleccionada.';
}
let maps;
window.addEventListener('load', () => {
  try { maps = createMaps(locationPicked); } catch {}
  if (!maps) $('map-message').textContent = 'El mapa no pudo cargar. Usá el listado y las coordenadas manuales.';
  render();
});
function card(r, includeMapButton = true) {
  const el = document.createElement('article'); el.className = 'card'; el.style.setProperty('--accent', r.pastel_color);
  const add = (tag, text) => { const n = document.createElement(tag); n.textContent = text; el.append(n); return n; };
  add('h3', `${r.animal_type === 'dog' ? '🐶' : r.animal_type === 'cat' ? '🐱' : '🐾'} ${r.title}`);
  if ('author' in r) add('small', r.author ? `Usuario: ${r.author.emoji} ${r.author.username}` : 'Usuario: aviso anterior sin cuenta');
  add('small', {lost:'Posiblemente perdido',seen:'Animal visto',found:'Encontrado',abandoned:'Posible abandono'}[r.status_type]);
  add('p', r.description); add('small', '📍 Ubicación aproximada');
  add('small', `Reportado hace ${Math.max(0, Math.floor((now() - Date.parse(r.created_at)) / 60000))} min`);
  add('small', remaining(r.expires_at, now()));
  const link = add('a', 'Abrir en Google Maps'); link.href = `https://www.google.com/maps?q=${r.latitude},${r.longitude}`; link.target = '_blank'; link.rel = 'noopener noreferrer';
  const share = add('button', 'Compartir'); share.type = 'button';
  share.addEventListener('click', async () => {
    const url = `${location.origin}/r/${r.id}`;
    try {
      if (navigator.share) await navigator.share({title: '🐾 HuellasUY', text: `${r.title}. Ubicación aproximada. Esta alerta expira automáticamente.`, url});
      else { await copy(url); share.textContent = 'Enlace copiado'; }
    } catch (e) { if (e.name !== 'AbortError') share.textContent = 'No pudimos compartir'; }
  });
  if (r.can_delete) {
    const remove = add('button', 'Eliminar mi alerta'); remove.type = 'button';
    remove.addEventListener('click', async () => {
      if (!confirm('¿Eliminar esta alerta?')) return;
      remove.disabled = true;
      try { await api(`/${r.id}`, {method:'DELETE',headers:{'Content-Type':'application/json'},body:'{}'}); await refresh(); }
      catch(error) { remove.disabled = false; $('connection').textContent = error.message; }
    });
  }
  if (includeMapButton) {
    const view = add('button', '📍 Ver en el mapa'); view.type = 'button';
    view.addEventListener('click', () => {
      if (Date.parse(r.expires_at) <= now()) { render(); $('map-message').textContent = 'Esta alerta ya expiró.'; return; }
      if (!maps?.focusReport(r.id)) { $('map-message').textContent = 'El mapa no está disponible. Podés abrir la ubicación aproximada en Google Maps.'; return; }
      const map = $('map');
      map.scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'center'});
      map.focus({preventScroll: true});
    });
  }
  return el;
}
function render() {
  reports = reports.filter(r => Date.parse(r.expires_at) > now());
  let visible = reports.filter(r => (!$('animal-filter').value || r.animal_type === $('animal-filter').value) && (!$('status-filter').value || r.status_type === $('status-filter').value));
  $('count').textContent = reports.length;
  if (focusedId) visible = visible.filter(r => r.id === focusedId);
  $('reports').replaceChildren(...visible.map(r => card(r)));
  if (!visible.length) {
    const empty = document.createElement('p');
    empty.textContent = focusedId ? (online ? '🐾 Esta alerta ya expiró o fue eliminada. Las alertas duran 24 horas.' : 'No pudimos verificar esta alerta. Reintentaremos automáticamente.') : '🐾 No hay alertas activas para mostrar. Si ves un animal desorientado, podés crear una alerta temporal.';
    $('reports').append(empty);
  }
  maps?.render(visible, card);
}
async function refresh() {
  if (busy || document.hidden) return;
  busy = true;
  try {
    const data = await api(); offset = data.server_time * 1000 - Date.now(); reports = data.reports; online = true;
    $('connection').textContent = '● Actualizado · Se sincroniza cada 15 segundos';
  } catch (error) {
    if (error.status === 401) { reports = []; render(); location.reload(); return; }
    online = false; $('connection').textContent = 'Sin conexión con el servidor. Las alertas pueden estar desactualizadas. Reintentaremos automáticamente.'; }
  finally { busy = false; render(); }
}
$('report').addEventListener('click', () => { dialog.showModal(); requestAnimationFrame(() => maps?.picker.invalidateSize()); });
$('close').addEventListener('click', () => dialog.close());
for (const id of ['animal-filter', 'status-filter']) $(id).addEventListener('change', render);
$('locate').addEventListener('click', () => {
  if (!navigator.geolocation) { $('location-message').textContent = 'Podés seleccionar manualmente el punto en el mapa.'; return; }
  $('location-message').textContent = 'Buscando tu ubicación…';
  navigator.geolocation.getCurrentPosition(p => {
    locationPicked(p.coords.latitude, p.coords.longitude); maps?.pick(p.coords.latitude, p.coords.longitude); maps?.picker.setView([p.coords.latitude, p.coords.longitude], 15);
  }, () => { $('location-message').textContent = 'No pudimos obtener tu ubicación. Podés seleccionar manualmente el punto en el mapa.'; }, {timeout:10000, maximumAge:0});
});
form.addEventListener('submit', async e => {
  e.preventDefault(); $('submit').disabled = true; $('form-error').textContent = '';
  const data = Object.fromEntries(new FormData(form)); data.latitude = Number(data.latitude); data.longitude = Number(data.longitude);
  try {
    const result = await api('', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
    $('private-link').value = `${location.origin}/manage/${result.report.id}#token=${encodeURIComponent(result.delete_token)}`;
    dialog.close(); form.reset(); $('success').showModal(); await refresh();
  } catch (error) { $('form-error').textContent = error.message === 'Failed to fetch' ? 'No pudimos conectar. Tu formulario sigue aquí; intentá nuevamente.' : error.message; }
  finally { $('submit').disabled = false; }
});
$('copy-private').addEventListener('click', async () => { try { await copy($('private-link').value); $('copy-private').textContent = 'Enlace copiado'; } catch { $('private-link').select(); } });
$('close-success').addEventListener('click', () => { $('success').close(); $('private-link').value = ''; $('copy-private').textContent = 'Copiar enlace privado'; });
if (privateToken && focusedId) {
  $('management').hidden = false;
  $('delete').addEventListener('click', async () => {
    $('delete').disabled = true;
    try { await api(`/${focusedId}`, {method:'DELETE', headers:{'Content-Type':'application/json'}, body:JSON.stringify({delete_token:privateToken})}); $('delete-message').textContent = 'Alerta eliminada. Gracias por actualizarla.'; await refresh(); }
    catch (error) { $('delete-message').textContent = error.message; $('delete').disabled = false; }
  });
}
refresh(); setInterval(refresh, 15000); setInterval(render, 10000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) { render(); refresh(); } });
