const $ = id => document.getElementById(id);
const message = text => { $('account-message').textContent = text; };
async function send(action, data) {
  const response = await fetch(`/api/auth/${action}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'No pudimos continuar.');
  return result;
}
function fields() {
  const action = $('account-action').value;
  $('username-label').hidden = !['login','register'].includes(action);
  $('email-label').hidden = action === 'login';
  $('password-label').hidden = !['login','register'].includes(action);
  $('account-form').elements.password.autocomplete = action === 'register' ? 'new-password' : 'current-password';
}
$('account-action').addEventListener('change', fields); fields();
$('account-form').addEventListener('submit', async e => {
  e.preventDefault(); $('account-submit').disabled = true;
  const data = Object.fromEntries(new FormData(e.target));
  try { const result = await send(data.action, data); message(result.message || 'Sesión iniciada.'); e.target.elements.password.value = ''; if (data.action === 'login') location.reload(); }
  catch(error) { message(error.message === 'Failed to fetch' ? 'Sin conexión. Tu formulario sigue aquí.' : error.message); }
  finally { $('account-submit').disabled = false; }
});
$('logout')?.addEventListener('click', async () => { try { await send('logout', {}); location.assign('/'); } catch { message('No pudimos cerrar la sesión. Reintentá.'); } });
const fragment = new URLSearchParams(location.hash.slice(1));
const purpose = fragment.has('verify') ? 'verify' : fragment.has('reset') ? 'reset' : null;
const token = purpose ? fragment.get(purpose) : null;
if (purpose) {
  history.replaceState(null, '', location.pathname);
  $('account-form').hidden = true; $('token-form').hidden = false;
  $('token-title').textContent = purpose === 'verify' ? 'Verificar correo' : 'Cambiar contraseña';
  $('new-password-label').hidden = purpose === 'verify';
  $('token-form').elements.password.required = purpose === 'reset';
}
$('token-form').addEventListener('submit', async e => {
  e.preventDefault(); const button = e.target.querySelector('button'); button.disabled = true;
  try { const result = await send(purpose, {token, password:e.target.elements.password.value}); message(result.message); e.target.reset(); e.target.hidden = true; $('account-form').hidden = false; }
  catch(error) { message(error.message); button.disabled = false; }
});
