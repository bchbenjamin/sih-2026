document.addEventListener('DOMContentLoaded', () => {
    // Initialize map
    const map = L.map('map').setView([30.745, 79.055], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);

    // Fetch data
    fetch('/api/data')
        .then(res => res.json())
        .then(data => {
            // Update metrics
            if (data.comparison && data.comparison.breach_metrics) {
                const metrics = data.comparison.breach_metrics;
                const hybridQ = metrics.hybrid.peak_discharge_m3s;
                const standQ = metrics.standalone.peak_discharge_m3s;
                
                document.getElementById('hybrid-discharge').innerText = `${Math.round(hybridQ).toLocaleString()} m³/s`;
                document.getElementById('standalone-discharge').innerText = `${Math.round(standQ).toLocaleString()} m³/s`;
                
                const delta = Math.round(hybridQ - standQ);
                const deltaEl = document.getElementById('delta-discharge');
                deltaEl.innerText = `${delta > 0 ? '+' : ''}${delta.toLocaleString()} m³/s`;
                deltaEl.style.color = delta > 0 ? 'var(--damage-high)' : 'var(--damage-low)';
            }

            // Populate Map and Damage List
            const damageList = document.getElementById('damage-list');
            
            if (data.damage && data.damage.length > 0) {
                const markers = [];
                
                data.damage.forEach(b => {
                    // List Item
                    const li = document.createElement('li');
                    li.className = 'damage-item';
                    
                    const depthClass = b.damage_class || (b.max_depth_m > 2 ? 'severe' : b.max_depth_m > 0.5 ? 'moderate' : 'low');
                    
                    li.innerHTML = `
                        <div>
                            <strong>Bldg #${b.building_id || Math.floor(Math.random()*1000)}</strong>
                            <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 4px;">
                                Depth: ${b.max_depth_m.toFixed(2)}m | Arrival: ${b.arrival_time_s.toFixed(0)}s
                            </div>
                        </div>
                        <span class="damage-badge badge-${depthClass}">${depthClass.toUpperCase()}</span>
                    `;
                    damageList.appendChild(li);

                    // Map Marker
                    let color = '#4ade80';
                    if (depthClass === 'severe') color = '#ef4444';
                    else if (depthClass === 'moderate') color = '#fbbf24';

                    const circle = L.circleMarker([b.lat, b.lon], {
                        radius: 6,
                        fillColor: color,
                        color: '#000',
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    }).addTo(map);
                    
                    circle.bindPopup(`
                        <b>Building</b><br>
                        Depth: ${b.max_depth_m.toFixed(2)}m<br>
                        Arrival Time: ${b.arrival_time_s.toFixed(0)}s
                    `);
                    
                    markers.push([b.lat, b.lon]);
                });
                
                if (markers.length > 0) {
                    map.fitBounds(L.latLngBounds(markers));
                }
            } else {
                damageList.innerHTML = '<li class="damage-item" style="justify-content: center; color: var(--text-muted);">No damage data found. Waiting for pipeline completion...</li>';
            }
        });
});

function exportData(format) {
    window.location.href = `/api/export/${format}`;
}
