
const adminDashboard = document.getElementById('admin-dashboard');
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

const refreshCacheButton = document.getElementById('refresh-content-cache-btn');
if (refreshCacheButton) {
refreshCacheButton.addEventListener('click', async function () {
    refreshCacheButton.disabled = true;
    try {
        const response = await fetch(adminDashboard.dataset.cacheRefreshUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken }
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || 'Actualisation impossible');
        alert(data.message);
    } catch (error) {
        alert(error.message);
    } finally {
        refreshCacheButton.disabled = false;
    }
});
}

document.querySelectorAll('.toggle-btn').forEach(function(btn){
btn.addEventListener('click', function(){
    const key = btn.getAttribute('data-key');
    const current = btn.getAttribute('data-value');
    const newVal = current === '1' ? '0' : '1';
    fetch(adminDashboard.dataset.toggleUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrfToken
    },
    body: 'key=' + encodeURIComponent(key) + '&value=' + encodeURIComponent(newVal)
    }).then(r => r.json()).then(data => {
    if(data.success){
        btn.setAttribute('data-value', data.value ? '1' : '0');
        btn.textContent = data.value ? 'ON' : 'OFF';
    } else {
        alert('Erreur: '+(data.error||''));
    }
    }).catch(() => alert('Erreur réseau'));
});
});

const shutdownBtn = document.getElementById('shutdown-server-btn');
const shutdownMessage = document.getElementById('shutdown-message');
if (shutdownBtn) {
shutdownBtn.addEventListener('click', function () {
    if (!confirm('Êtes-vous sûr de vouloir éteindre le serveur ?')) {
    return;
    }
    shutdownMessage.classList.remove('hidden');
    fetch(adminDashboard.dataset.shutdownUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrfToken
    }
    }).then(r => r.json()).then(data => {
    if (!data.success) {
        shutdownMessage.textContent = data.error || 'Erreur lors de l\'arrêt du serveur.';
    }
    }).catch(() => {
    shutdownMessage.textContent = 'La demande a été envoyée, mais la réponse est indisponible pendant l\'arrêt.';
    });
});
}

window.addEventListener('load', function () {
if (!window.Chart) return;
const labels = [];
const latencies = [];
const promptTokens = [];
const cachedTokens = [];
const responseTokens = [];
const chartRows = JSON.parse(document.getElementById('admin-chart-data')?.textContent || '[]');
chartRows.forEach((row) => {
    labels.push(row[0]);
    latencies.push(row[2] ?? 0);
    promptTokens.push(row[5] ?? 0);
    cachedTokens.push(row[6] ?? 0);
    responseTokens.push(row[7] ?? 0);
});
const chartOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#dfeee0' } } }, scales: { x: { ticks: { color: '#a9c8ad', maxRotation: 45, autoSkip: true }, grid: { color: 'rgba(184, 216, 191, 0.08)' } }, y: { beginAtZero: true, ticks: { color: '#a9c8ad' }, grid: { color: 'rgba(184, 216, 191, 0.08)' } } } };
new Chart(document.getElementById('latency-chart'), { type: 'line', data: { labels, datasets: [{ label: 'ms', data: latencies, borderColor: '#9dd0a3', backgroundColor: 'rgba(157, 208, 163, 0.14)', fill: true, tension: 0.3 }] }, options: chartOptions });
new Chart(document.getElementById('tokens-chart'), { type: 'bar', data: { labels, datasets: [{ label: 'Prompt', data: promptTokens, backgroundColor: '#9dd0a3' }, { label: 'Cache', data: cachedTokens, backgroundColor: '#d6a85d' }, { label: 'Réponse', data: responseTokens, backgroundColor: '#d97878' }] }, options: chartOptions });
});