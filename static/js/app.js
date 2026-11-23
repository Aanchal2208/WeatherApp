/**
 * Weather App — Frontend JavaScript
 *
 * Handles all UI interactions, API calls, and dynamic content rendering.
 * Author: Aanchal
 */

// ============================================================
// State
// ============================================================
let currentLocation = null;  // Last geocoded location
let allRecords = [];         // Cached records from DB
let map = null;              // Leaflet map instance
let mapMarker = null;        // Map marker

// ============================================================
// Utility Functions
// ============================================================

function showAlert(message, type = 'danger') {
    const container = document.getElementById('alert-container');
    const id = 'alert-' + Date.now();
    container.innerHTML = `
        <div id="${id}" class="alert alert-${type} alert-floating alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    setTimeout(() => {
        const el = document.getElementById(id);
        if (el) el.remove();
    }, 5000);
}

function showLoading(show = true) {
    document.getElementById('loading-overlay').style.display = show ? 'flex' : 'none';
}

async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options,
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }
        return data;
    } catch (error) {
        if (error.message.includes('Failed to fetch')) {
            throw new Error('Network error. Please check your connection.');
        }
        throw error;
    }
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric'
    });
}

// ============================================================
// Current Weather
// ============================================================

async function searchCurrentWeather() {
    const query = document.getElementById('location-input').value.trim();
    if (!query) {
        showAlert('Please enter a location.', 'warning');
        return;
    }

    showLoading(true);
    try {
        const data = await apiCall(`/api/weather/current?q=${encodeURIComponent(query)}`);
        currentLocation = data.location;
        displayCurrentWeather(data);
        updateMap(data.location.latitude, data.location.longitude, data.location.name);
        // Pre-fill the historical date range form with today
        document.getElementById('hist-location').value = query;
        showAlert('Weather loaded successfully!', 'success');
    } catch (error) {
        showAlert(error.message);
        document.getElementById('current-weather-display').innerHTML =
            `<div class="text-center text-secondary p-4"><i>No weather data to display.</i></div>`;
    } finally {
        showLoading(false);
    }
}

function displayCurrentWeather(data) {
    const w = data.weather;
    const loc = data.location;
    const aq = data.air_quality || {};
    const sun = data.sun || {};

    const container = document.getElementById('current-weather-display');

    let aqiHtml = '';
    if (aq.aqi != null) {
        const aqiColors = {green:'#22c55e', yellow:'#eab308', orange:'#f97316', red:'#ef4444', purple:'#a855f7', maroon:'#991b1b'};
        const bgColor = aqiColors[aq.aqi_color] || '#6b7280';
        aqiHtml = `
            <div class="weather-detail-item">
                <div class="label">Air Quality</div>
                <div class="value"><span class="aqi-badge" style="background:${bgColor};color:#fff">${aq.aqi} — ${aq.aqi_label}</span></div>
            </div>
        `;
        if (aq.uv_index != null) {
            aqiHtml += `
                <div class="weather-detail-item">
                    <div class="label">UV Index</div>
                    <div class="value">${aq.uv_index}</div>
                </div>
            `;
        }
    }

    let sunHtml = '';
    if (sun.sunrise) {
        sunHtml = `
            <div class="weather-detail-item">
                <div class="label">Sunrise</div>
                <div class="value">🌅 ${sun.sunrise ? sun.sunrise.split('T')[1] || sun.sunrise : '—'}</div>
            </div>
            <div class="weather-detail-item">
                <div class="label">Sunset</div>
                <div class="value">🌇 ${sun.sunset ? sun.sunset.split('T')[1] || sun.sunset : '—'}</div>
            </div>
            <div class="weather-detail-item">
                <div class="label">Daylight</div>
                <div class="value">☀️ ${sun.daylight_duration || '—'}</div>
            </div>
        `;
    }

    container.innerHTML = `
        <div class="weather-current">
            <h5 class="text-secondary mb-1">${loc.display_name || loc.name}</h5>
            <p class="text-secondary small mb-3">
                📍 ${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)}
                ${loc.country ? ' · ' + loc.country : ''}
                ${w.timezone ? ' · ' + w.timezone : ''}
            </p>
            <div class="weather-icon-large mb-2">${w.weather_icon}</div>
            <div class="temperature-large">${w.temperature}${w.temperature_unit}</div>
            <p class="text-secondary mt-1 mb-0">${w.weather_description}</p>
            <p class="text-secondary small">Feels like ${w.apparent_temperature}${w.temperature_unit}</p>
        </div>

        <div class="weather-detail-grid mt-3">
            <div class="weather-detail-item">
                <div class="label">Humidity</div>
                <div class="value">💧 ${w.humidity}%</div>
            </div>
            <div class="weather-detail-item">
                <div class="label">Wind</div>
                <div class="value">💨 ${w.wind_speed} ${w.wind_speed_unit}</div>
            </div>
            <div class="weather-detail-item">
                <div class="label">Wind Gusts</div>
                <div class="value">🌬️ ${w.wind_gusts || '—'} ${w.wind_speed_unit}</div>
            </div>
            <div class="weather-detail-item">
                <div class="label">Wind Direction</div>
                <div class="value">🧭 ${w.wind_direction || '—'}°</div>
            </div>
            <div class="weather-detail-item">
                <div class="label">Pressure</div>
                <div class="value">🔵 ${w.pressure_msl || '—'} hPa</div>
            </div>
            <div class="weather-detail-item">
                <div class="label">Cloud Cover</div>
                <div class="value">☁️ ${w.cloud_cover || '—'}%</div>
            </div>
            <div class="weather-detail-item">
                <div class="label">Precipitation</div>
                <div class="value">🌧️ ${w.precipitation || 0} mm</div>
            </div>
            <div class="weather-detail-item">
                <div class="label">Snowfall</div>
                <div class="value">❄️ ${w.snowfall || 0} cm</div>
            </div>
            ${aqiHtml}
            ${sunHtml}
        </div>
    `;
}

// ============================================================
// CRUD — CREATE
// ============================================================

async function createWeatherRecord() {
    const location = document.getElementById('hist-location').value.trim();
    const dateStart = document.getElementById('hist-date-start').value;
    const dateEnd = document.getElementById('hist-date-end').value;

    if (!location || !dateStart || !dateEnd) {
        showAlert('Please fill in location, start date, and end date.', 'warning');
        return;
    }

    showLoading(true);
    try {
        const data = await apiCall('/api/weather', {
            method: 'POST',
            body: JSON.stringify({
                location: location,
                date_start: dateStart,
                date_end: dateEnd,
            }),
        });

        showAlert('Weather record created and saved!', 'success');
        displayHistoricalWeather(data.record);
        await loadRecords(); // Refresh the records table
    } catch (error) {
        showAlert(error.message);
    } finally {
        showLoading(false);
    }
}

function displayHistoricalWeather(record) {
    const container = document.getElementById('historical-weather-display');
    const weather = record.weather_data;
    const times = weather.time || [];

    if (!times.length) {
        container.innerHTML = '<p class="text-secondary text-center">No daily data available for this range.</p>';
        return;
    }

    // Build table
    let tableRows = '';
    for (let i = 0; i < times.length; i++) {
        const icon = (weather.weather_icon || [])[i] || '';
        const desc = (weather.weather_description || [])[i] || '—';
        const tMax = (weather.temperature_2m_max || [])[i];
        const tMin = (weather.temperature_2m_min || [])[i];
        const precip = (weather.precipitation_sum || [])[i] || 0;
        const wind = (weather.wind_speed_10m_max || [])[i] || '—';

        tableRows += `
            <tr>
                <td>${times[i]}</td>
                <td>${icon} ${desc}</td>
                <td class="text-danger">${tMax != null ? tMax + '°C' : '—'}</td>
                <td class="text-info">${tMin != null ? tMin + '°C' : '—'}</td>
                <td>${precip} mm</td>
                <td>${wind} km/h</td>
            </tr>
        `;
    }

    container.innerHTML = `
        <h6 class="mb-3">📊 Daily Weather: ${record.location_name} (${record.date_start} → ${record.date_end})</h6>
        <div class="table-responsive">
            <table class="table table-dark table-sm table-hover">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Conditions</th>
                        <th>Max Temp</th>
                        <th>Min Temp</th>
                        <th>Precip</th>
                        <th>Wind</th>
                    </tr>
                </thead>
                <tbody>${tableRows}</tbody>
            </table>
        </div>
        <div class="chart-container mt-3">
            <canvas id="temp-chart"></canvas>
        </div>
    `;

    // Draw temperature chart
    renderTemperatureChart(times, weather.temperature_2m_max || [], weather.temperature_2m_min || []);
}

function renderTemperatureChart(dates, maxTemps, minTemps) {
    const ctx = document.getElementById('temp-chart');
    if (!ctx) return;

    // Destroy existing chart if any
    if (window.tempChart) window.tempChart.destroy();

    window.tempChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Max Temperature (°C)',
                    data: maxTemps,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    tension: 0.3,
                },
                {
                    label: 'Min Temperature (°C)',
                    data: minTemps,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.3,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#94a3b8' } },
            },
            scales: {
                x: {
                    ticks: { color: '#94a3b8', maxTicksLimit: 15 },
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                },
                y: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                },
            },
        },
    });
}

// ============================================================
// CRUD — READ
// ============================================================

async function loadRecords() {
    try {
        const data = await apiCall('/api/weather');
        allRecords = data.records || [];
        renderRecordsTable(allRecords);
    } catch (error) {
        console.error('Failed to load records:', error);
    }
}

function renderRecordsTable(records) {
    const tbody = document.getElementById('records-tbody');
    const countEl = document.getElementById('records-count');

    countEl.textContent = `${records.length} record(s)`;

    if (!records.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-secondary py-4">
                    <em>No records yet. Use the "Historical Weather" section to create records.</em>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = records.map(r => `
        <tr>
            <td><strong>#${r.id}</strong></td>
            <td>
                <strong>${escapeHtml(r.location_name)}</strong>
                <br><small class="text-secondary">${escapeHtml(r.location_query)}</small>
            </td>
            <td><small>${r.latitude.toFixed(2)}, ${r.longitude.toFixed(2)}</small></td>
            <td>${r.date_start}</td>
            <td>${r.date_end}</td>
            <td><small>${formatDate(r.created_at)}</small></td>
            <td class="text-end">
                <button class="btn btn-sm btn-outline-info me-1" onclick="viewRecord(${r.id})" title="View">
                    👁️
                </button>
                <button class="btn btn-sm btn-outline-warning me-1" onclick="openEditModal(${r.id})" title="Edit">
                    ✏️
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteRecord(${r.id})" title="Delete">
                    🗑️
                </button>
            </td>
        </tr>
    `).join('');
}

async function viewRecord(id) {
    showLoading(true);
    try {
        const data = await apiCall(`/api/weather/${id}`);
        displayHistoricalWeather(data.record);
        // Switch to the weather tab
        const weatherTab = document.querySelector('[data-bs-target="#tab-weather"]');
        if (weatherTab) bootstrap.Tab.getOrCreateInstance(weatherTab).show();
        // Scroll to historical display
        document.getElementById('historical-weather-display').scrollIntoView({ behavior: 'smooth' });
        showAlert(`Viewing record #${id}`, 'info');
    } catch (error) {
        showAlert(error.message);
    } finally {
        showLoading(false);
    }
}

// ============================================================
// CRUD — UPDATE
// ============================================================

function openEditModal(id) {
    const record = allRecords.find(r => r.id === id);
    if (!record) {
        showAlert('Record not found in local cache. Refreshing...', 'warning');
        loadRecords();
        return;
    }

    document.getElementById('edit-record-id').value = record.id;
    document.getElementById('edit-location').value = record.location_query;
    document.getElementById('edit-date-start').value = record.date_start;
    document.getElementById('edit-date-end').value = record.date_end;

    const modal = new bootstrap.Modal(document.getElementById('editModal'));
    modal.show();
}

async function updateRecord() {
    const id = document.getElementById('edit-record-id').value;
    const location = document.getElementById('edit-location').value.trim();
    const dateStart = document.getElementById('edit-date-start').value;
    const dateEnd = document.getElementById('edit-date-end').value;

    if (!location || !dateStart || !dateEnd) {
        showAlert('All fields are required.', 'warning');
        return;
    }

    showLoading(true);
    try {
        await apiCall(`/api/weather/${id}`, {
            method: 'PUT',
            body: JSON.stringify({
                location: location,
                date_start: dateStart,
                date_end: dateEnd,
            }),
        });

        bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
        showAlert('Record updated successfully!', 'success');
        await loadRecords();
    } catch (error) {
        showAlert(error.message);
    } finally {
        showLoading(false);
    }
}

// ============================================================
// CRUD — DELETE
// ============================================================

async function deleteRecord(id) {
    if (!confirm(`Are you sure you want to delete record #${id}?`)) return;

    showLoading(true);
    try {
        const data = await apiCall(`/api/weather/${id}`, { method: 'DELETE' });
        showAlert(data.message, 'success');
        await loadRecords();
    } catch (error) {
        showAlert(error.message);
    } finally {
        showLoading(false);
    }
}

// ============================================================
// API Integrations — Explore Location
// ============================================================

async function exploreLocation() {
    const query = document.getElementById('location-input').value.trim();
    if (!query && !currentLocation) {
        showAlert('Please search for a location first.', 'warning');
        return;
    }

    const searchQuery = currentLocation ? currentLocation.name : query;
    const countryCode = currentLocation ? (currentLocation.country_code || '') : '';

    showLoading(true);
    try {
        const data = await apiCall(
            `/api/integrations/explore?q=${encodeURIComponent(searchQuery)}&country_code=${encodeURIComponent(countryCode)}`
        );

        // Wikipedia
        displayWikipedia(data.wikipedia);

        // YouTube
        displayYouTube(data.youtube);

        // Country Info
        if (data.country && Object.keys(data.country).length) {
            displayCountryInfo(data.country);
        }

        showAlert('Location info loaded!', 'success');
    } catch (error) {
        showAlert(error.message);
    } finally {
        showLoading(false);
    }
}

function displayWikipedia(wiki) {
    const container = document.getElementById('wikipedia-display');
    if (!wiki || !wiki.found) {
        container.innerHTML = '<p class="text-secondary">No Wikipedia article found.</p>';
        return;
    }

    container.innerHTML = `
        <div class="card">
            <div class="card-body d-flex flex-wrap gap-3">
                ${wiki.thumbnail_url ? `<img src="${wiki.thumbnail_url}" alt="${escapeHtml(wiki.title)}" class="wiki-thumbnail">` : ''}
                <div class="flex-grow-1">
                    <h5>${escapeHtml(wiki.title)}</h5>
                    ${wiki.description ? `<p class="text-secondary small">${escapeHtml(wiki.description)}</p>` : ''}
                    <p>${escapeHtml(wiki.extract)}</p>
                    ${wiki.url ? `<a href="${wiki.url}" target="_blank" class="btn btn-sm btn-outline-light">Read on Wikipedia →</a>` : ''}
                </div>
            </div>
        </div>
    `;
}

function displayYouTube(yt) {
    const container = document.getElementById('youtube-display');

    if (yt.source === 'api' && yt.videos.length) {
        container.innerHTML = `
            <div class="row g-3">
                ${yt.videos.map(v => `
                    <div class="col-md-4 col-sm-6">
                        <div class="card h-100">
                            <a href="${v.watch_url}" target="_blank">
                                <img src="${v.thumbnail}" class="card-img-top" alt="${escapeHtml(v.title)}" style="border-radius: 12px 12px 0 0;">
                            </a>
                            <div class="card-body p-2">
                                <a href="${v.watch_url}" target="_blank" class="text-decoration-none">
                                    <h6 class="card-title small text-primary">${escapeHtml(v.title)}</h6>
                                </a>
                                <p class="card-text small text-secondary">${escapeHtml(v.channel)}</p>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } else {
        container.innerHTML = `
            <div class="text-center p-4">
                <p class="text-secondary mb-3">YouTube API key not configured. Click below to search manually:</p>
                <a href="${yt.search_url}" target="_blank" class="btn btn-danger">
                    ▶️ Search on YouTube
                </a>
                <p class="text-secondary small mt-2">
                    <em>Tip: Set YOUTUBE_API_KEY in .env to see embedded video results.</em>
                </p>
            </div>
        `;
    }
}

function displayCountryInfo(country) {
    const container = document.getElementById('country-display');

    const currencies = (country.currencies || []).map(c => `${c.name} (${c.symbol || c.code})`).join(', ');
    const languages = (country.languages || []).join(', ');

    container.innerHTML = `
        <div class="card">
            <div class="card-body">
                <h5>${country.flag_emoji || ''} ${escapeHtml(country.name)}</h5>
                <p class="text-secondary small">${escapeHtml(country.official_name)}</p>
                <div class="row g-2">
                    <div class="col-sm-6">
                        <strong>Capital:</strong> ${escapeHtml(country.capital || 'N/A')}<br>
                        <strong>Region:</strong> ${escapeHtml(country.region || '')} / ${escapeHtml(country.subregion || '')}<br>
                        <strong>Population:</strong> ${country.population ? country.population.toLocaleString() : 'N/A'}<br>
                        <strong>Area:</strong> ${country.area_km2 ? country.area_km2.toLocaleString() + ' km²' : 'N/A'}
                    </div>
                    <div class="col-sm-6">
                        <strong>Currencies:</strong> ${escapeHtml(currencies) || 'N/A'}<br>
                        <strong>Languages:</strong> ${escapeHtml(languages) || 'N/A'}<br>
                        <strong>Timezones:</strong> ${(country.timezones || []).join(', ')}<br>
                        ${country.maps_url ? `<a href="${country.maps_url}" target="_blank" class="btn btn-sm btn-outline-light mt-2">🗺️ Google Maps</a>` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ============================================================
// Map (Leaflet + OpenStreetMap)
// ============================================================

function initMap() {
    map = L.map('map').setView([20, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a> contributors',
        maxZoom: 18,
    }).addTo(map);
}

function updateMap(lat, lon, name) {
    if (!map) initMap();

    map.setView([lat, lon], 10);

    if (mapMarker) map.removeLayer(mapMarker);
    mapMarker = L.marker([lat, lon]).addTo(map);
    mapMarker.bindPopup(`<strong>${escapeHtml(name)}</strong><br>${lat.toFixed(4)}, ${lon.toFixed(4)}`).openPopup();
}

// ============================================================
// Data Export
// ============================================================

function exportData(format) {
    window.open(`/api/export/${format}`, '_blank');
}

// ============================================================
// Helpers
// ============================================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================
// Initialization
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    // Load existing records
    loadRecords();

    // Initialize map
    initMap();

    // Set default date range (last 7 days)
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);

    document.getElementById('hist-date-end').value = today.toISOString().split('T')[0];
    document.getElementById('hist-date-start').value = weekAgo.toISOString().split('T')[0];

    // Enter key on search input
    document.getElementById('location-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') searchCurrentWeather();
    });
});
