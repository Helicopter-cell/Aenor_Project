
document.querySelectorAll('.toggle-btn').forEach(function(btn){
btn.addEventListener('click', function(){
    const key = btn.getAttribute('data-key');
    const current = btn.getAttribute('data-value');
    const newVal = current === '1' ? '0' : '1';
    fetch('{{ url_for("admin_toggle_config") }}', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
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
    fetch('{{ url_for("admin_shutdown") }}', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
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
{% for timestamp, endpoint, response_time_ms, status, tokens, prompt_tokens, cached_tokens, response_tokens, traduction_fiable in api_logs %}
    labels.push({{ timestamp|tojson }});
    latencies.push({{ response_time_ms|default(0, true)|tojson }});
    promptTokens.push({{ prompt_tokens|default(0, true)|tojson }});
    cachedTokens.push({{ cached_tokens|default(0, true)|tojson }});
    responseTokens.push({{ response_tokens|default(0, true)|tojson }});
{% endfor %}
const chartOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#dfeee0' } } }, scales: { x: { ticks: { color: '#a9c8ad', maxRotation: 45, autoSkip: true }, grid: { color: 'rgba(184, 216, 191, 0.08)' } }, y: { beginAtZero: true, ticks: { color: '#a9c8ad' }, grid: { color: 'rgba(184, 216, 191, 0.08)' } } } };
new Chart(document.getElementById('latency-chart'), { type: 'line', data: { labels, datasets: [{ label: 'ms', data: latencies, borderColor: '#9dd0a3', backgroundColor: 'rgba(157, 208, 163, 0.14)', fill: true, tension: 0.3 }] }, options: chartOptions });
new Chart(document.getElementById('tokens-chart'), { type: 'bar', data: { labels, datasets: [{ label: 'Prompt', data: promptTokens, backgroundColor: '#9dd0a3' }, { label: 'Cache', data: cachedTokens, backgroundColor: '#d6a85d' }, { label: 'Réponse', data: responseTokens, backgroundColor: '#d97878' }] }, options: chartOptions });
});