let saved;
try { saved = localStorage.getItem('theme'); } catch {}
const media = matchMedia('(prefers-color-scheme: dark)');
function apply() { document.documentElement.dataset.theme = saved || (media.matches ? 'dark' : 'light'); }
apply(); media.addEventListener('change', apply);
document.querySelector('#theme').addEventListener('click', () => {
  saved = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  try { localStorage.setItem('theme', saved); } catch {}
  apply();
});
