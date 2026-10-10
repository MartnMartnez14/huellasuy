document.querySelectorAll('[data-report],[data-user]').forEach(button => button.addEventListener('click', async () => {
  if (!confirm('¿Confirmás esta acción de administración?')) return;
  button.disabled = true;
  const action = button.dataset.report ? 'remove' : 'suspend';
  const data = action === 'remove' ? {report_id:Number(button.dataset.report)} : {user_id:Number(button.dataset.user),disabled:button.dataset.disabled === 'true'};
  try {
    const response = await fetch(`/api/auth/admin/${action}`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    location.reload();
  } catch(error) { document.getElementById('admin-message').textContent = error.message; button.disabled = false; }
}));
