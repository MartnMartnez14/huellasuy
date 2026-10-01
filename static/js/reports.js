export async function api(path = '', options = {}) {
  const response = await fetch(`/api/reports${path}`, {cache: 'no-store', ...options});
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) { const error = new Error(data.error || 'No pudimos completar la solicitud.'); error.status = response.status; throw error; }
  return data;
}
export async function copy(text) {
  if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
  window.prompt('Copiá este enlace:', text);
}
export function remaining(expires, now) {
  const minutes = Math.max(0, Math.ceil((Date.parse(expires) - now) / 60000));
  return `Expira en ${Math.floor(minutes / 60)} h ${minutes % 60} min`;
}
