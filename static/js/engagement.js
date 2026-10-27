(() => {
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link) return;
    const href = link.getAttribute('href');
    let kind, target;
    if (href.startsWith('mailto:')) { kind = 'contact_click'; target = 'email'; }
    else if (href.startsWith('tel:')) { kind = 'contact_click'; target = 'phone'; }
    else if (href === '/contact' || href.startsWith('/contact?')) { kind = 'contact_click'; target = 'contact_page'; }
    else if (/^\/project\/\d+$/.test(href)) { kind = 'project_link'; target = href.split('/').pop(); }
    if (!kind) return;
    const token = document.querySelector('meta[name="csrf-token"]')?.content;
    if (!token) return;
    fetch('/events', {method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':token},body:JSON.stringify({kind,target}),keepalive:true,credentials:'same-origin'}).catch(() => {});
  });
})();
