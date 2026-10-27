(() => {
  const canvas = document.getElementById('traffic-chart');
  const source = document.getElementById('traffic-data');
  if (!canvas || !source || typeof Chart === 'undefined') return;
  const data = JSON.parse(source.textContent);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [
        { label: 'Page views', data: data.views, borderColor: '#007963', backgroundColor: 'rgba(0,121,99,0.08)', borderWidth: 3, pointRadius: data.labels.length > 30 ? 0 : 3, pointHoverRadius: 5, lineTension: 0.2, fill: true },
        { label: 'Unique IPs', data: data.unique, borderColor: '#5984db', backgroundColor: 'transparent', borderDash: [5, 4], borderWidth: 2, pointRadius: 0, pointHoverRadius: 5, lineTension: 0.2, fill: false }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { duration: reducedMotion ? 0 : 350 },
      legend: { display: false },
      tooltips: { mode: 'index', intersect: false, backgroundColor: '#163734', cornerRadius: 8, xPadding: 14, yPadding: 14 },
      hover: { mode: 'index', intersect: false },
      scales: {
        xAxes: [{ gridLines: { display: false }, ticks: { maxTicksLimit: 8, maxRotation: 0, fontColor: '#718582', callback: value => { const parts = value.split('-'); return `${parts[2]}/${parts[1]}`; } } }],
        yAxes: [{ gridLines: { color: '#edf2f1', drawBorder: false }, ticks: { beginAtZero: true, precision: 0, fontColor: '#718582' } }]
      }
    }
  });
})();
