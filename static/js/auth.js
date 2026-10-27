(() => {
  const button = document.querySelector('.show-password');
  const password = document.getElementById('password');
  if (!button || !password) return;
  button.addEventListener('click', () => {
    const visible = password.type === 'password';
    password.type = visible ? 'text' : 'password';
    button.textContent = visible ? 'Hide' : 'Show';
    button.setAttribute('aria-pressed', String(visible));
  });
})();
