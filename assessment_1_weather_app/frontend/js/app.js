/**
 * Weather Intelligence Platform — Frontend Controller
 * Vanilla JavaScript communicating with FastAPI REST endpoints.
 * 
 * Developer: Aanchal Singh
 * Organization: PM Accelerator
 */

// Global State
const state = {
  currentPage: 1,
  perPage: 10,
  totalPages: 1,
  filterQuery: "",
  activeMap: null,
  mapMarker: null,
  recordPendingDelete: null,
};

// DOM Content Loaded Entrypoint
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  setDefaultDates();
  bindEventHandlers();
  checkSystemHealth();
  loadSavedRecords(1);
  
  // Load default city weather (New York) on startup
  fetchCurrentWeather("New York");
});

/* -------------------------------------------------------------------------
   1. Interactive Map Initialization (Leaflet.js)
-------------------------------------------------------------------------- */
function initMap() {
  const mapElem = document.getElementById("map");
  if (!mapElem) return;

  state.activeMap = L.map("map").setView([40.7128, -74.0060], 4);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
    maxZoom: 18,
  }).addTo(state.activeMap);

  state.mapMarker = L.marker([40.7128, -74.0060]).addTo(state.activeMap);
  state.mapMarker.bindPopup("<b>New York</b><br>Initial Map Center").openPopup();
}

function updateMap(lat, lon, name, detailsHtml = "") {
  if (!state.activeMap) return;
  state.activeMap.setView([lat, lon], 10);
  if (state.mapMarker) {
    state.mapMarker.setLatLng([lat, lon]);
  } else {
    state.mapMarker = L.marker([lat, lon]).addTo(state.activeMap);
  }
  const popupContent = `<b>${name}</b><br>Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)}<br>${detailsHtml}`;
  state.mapMarker.bindPopup(popupContent).openPopup();
}

/* -------------------------------------------------------------------------
   2. Default Date Helpers
-------------------------------------------------------------------------- */
function setDefaultDates() {
  const today = new Date();
  const pastWeek = new Date();
  pastWeek.setDate(today.getDate() - 6);

  const fmt = (d) => d.toISOString().split("T")[0];

  const startInput = document.getElementById("range-start-date");
  const endInput = document.getElementById("range-end-date");
  if (startInput && endInput) {
    startInput.value = fmt(pastWeek);
    endInput.value = fmt(today);
  }
}

/* -------------------------------------------------------------------------
   3. Event Handlers & Forms
-------------------------------------------------------------------------- */
function bindEventHandlers() {
  // Current weather search form
  const curForm = document.getElementById("current-weather-form");
  if (curForm) {
    curForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const q = document.getElementById("current-query-input").value.trim();
      if (q) fetchCurrentWeather(q);
    });
  }

  // Use GPS button
  const gpsBtn = document.getElementById("btn-use-gps");
  if (gpsBtn) {
    gpsBtn.addEventListener("click", () => {
      if (!navigator.geolocation) {
        showToast("Geolocation is not supported by your browser.", "error");
        return;
      }
      showToast("Requesting device GPS coordinates...", "info");
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords;
          fetchCurrentWeatherByCoords(latitude, longitude);
        },
        (err) => {
          showToast(`GPS Error: ${err.message}`, "error");
        }
      );
    });
  }

  // Date Range Search Form (CRUD: CREATE)
  const rangeForm = document.getElementById("range-search-form");
  if (rangeForm) {
    rangeForm.addEventListener("submit", (e) => {
      e.preventDefault();
      createWeatherRecord();
    });
  }

  // Records Table Filter & Refresh
  document.getElementById("btn-refresh-records")?.addEventListener("click", () => {
    loadSavedRecords(state.currentPage);
  });
  document.getElementById("btn-apply-filter")?.addEventListener("click", () => {
    state.filterQuery = document.getElementById("filter-records-input").value.trim();
    loadSavedRecords(1);
  });
  document.getElementById("btn-clear-filter")?.addEventListener("click", () => {
    document.getElementById("filter-records-input").value = "";
    state.filterQuery = "";
    loadSavedRecords(1);
  });

  // Pagination buttons
  document.getElementById("btn-prev-page")?.addEventListener("click", () => {
    if (state.currentPage > 1) loadSavedRecords(state.currentPage - 1);
  });
  document.getElementById("btn-next-page")?.addEventListener("click", () => {
    if (state.currentPage < state.totalPages) loadSavedRecords(state.currentPage + 1);
  });

  // Modal Closures
  document.getElementById("btn-close-modal")?.addEventListener("click", closeUpdateModal);
  document.getElementById("btn-cancel-modal")?.addEventListener("click", closeUpdateModal);
  document.getElementById("btn-close-delete-modal")?.addEventListener("click", closeDeleteModal);
  document.getElementById("btn-cancel-delete")?.addEventListener("click", closeDeleteModal);

  // Update Form Submit (CRUD: UPDATE)
  document.getElementById("update-record-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    submitRecordUpdate();
  });

  // Delete Confirm Button (CRUD: DELETE)
  document.getElementById("btn-confirm-delete")?.addEventListener("click", () => {
    if (state.recordPendingDelete) {
      deleteRecord(state.recordPendingDelete.id);
    }
  });
}

/* -------------------------------------------------------------------------
   4. Current Weather API Calls
-------------------------------------------------------------------------- */
async function fetchCurrentWeather(query) {
  try {
    showToast(`Searching weather for "${query}"...`, "info");
    const resp = await fetch(`/api/weather/current?q=${encodeURIComponent(query)}`);
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || err.error || "Failed to fetch weather");
    }
    const data = await resp.json();
    renderCurrentWeather(data);
    loadYouTubeVideos(data.location.name);
    showToast(`Weather updated for ${data.location.name}.`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function fetchCurrentWeatherByCoords(lat, lon) {
  try {
    const resp = await fetch(`/api/weather/current?lat=${lat}&lon=${lon}`);
    if (!resp.ok) throw new Error("Failed to resolve GPS coordinates.");
    const data = await resp.json();
    renderCurrentWeather(data);
    loadYouTubeVideos(data.location.name);
    showToast(`Weather loaded for ${data.location.name} via GPS.`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

function renderCurrentWeather(data) {
  const loc = data.location;
  const w = data.weather;
  const aqi = data.air_quality;
  const rec = data.recommendations;

  document.getElementById("current-loc-name").textContent = loc.name;
  document.getElementById("current-loc-country").textContent = `${loc.admin1 ? loc.admin1 + ", " : ""}${loc.country || ""}`;
  document.getElementById("current-weather-icon").textContent = w.weather_icon || "🌤️";
  document.getElementById("current-temp").textContent = w.temperature.toFixed(1);
  document.getElementById("current-condition-text").textContent = w.weather_description;
  document.getElementById("current-apparent-temp").textContent = `${w.apparent_temperature.toFixed(1)}°C`;
  document.getElementById("current-local-time").textContent = data.local_time ? data.local_time.substring(11, 16) : "--:--";

  document.getElementById("metric-humidity").textContent = `${w.relative_humidity}%`;
  document.getElementById("metric-wind").textContent = `${w.wind_speed.toFixed(1)} km/h`;
  document.getElementById("metric-wind-dir").textContent = `${w.wind_direction}°`;
  document.getElementById("metric-precipitation").textContent = `${w.precipitation.toFixed(1)} mm`;
  document.getElementById("metric-pressure").textContent = `${w.surface_pressure.toFixed(0)} hPa`;
  
  if (aqi && aqi.aqi !== null) {
    document.getElementById("metric-aqi").textContent = `${aqi.aqi} (${aqi.category || "Standard"})`;
  } else {
    document.getElementById("metric-aqi").textContent = "N/A";
  }

  document.getElementById("metric-sunrise").textContent = data.sunrise ? data.sunrise.substring(11, 16) : "--:--";
  document.getElementById("metric-sunset").textContent = data.sunset ? data.sunset.substring(11, 16) : "--:--";

  if (rec) {
    document.getElementById("rec-activity").textContent = rec.activity_type + " — " + rec.advice;
    document.getElementById("rec-clothing").textContent = rec.clothing;
    document.getElementById("rec-precautions").textContent = rec.precautions;
  }

  document.getElementById("current-weather-display").classList.remove("hidden");

  // Center Map on Location
  updateMap(loc.latitude, loc.longitude, loc.name, `Temp: ${w.temperature}°C, ${w.weather_description}`);
}

/* -------------------------------------------------------------------------
   5. CRUD: CREATE (Save Record to PostgreSQL)
-------------------------------------------------------------------------- */
async function createWeatherRecord() {
  const locInput = document.getElementById("range-location").value.trim();
  const startInput = document.getElementById("range-start-date").value;
  const endInput = document.getElementById("range-end-date").value;

  if (!locInput || !startInput || !endInput) {
    showToast("Please provide location and both start and end dates.", "error");
    return;
  }

  if (startInput > endInput) {
    showToast("Start date cannot be after end date.", "error");
    return;
  }

  try {
    showToast(`Querying weather and saving to PostgreSQL...`, "info");
    const payload = {
      location: locInput,
      date_start: startInput,
      date_end: endInput,
    };

    const resp = await fetch("/api/weather/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || err.error || "Failed to create weather record");
    }

    const createdRecord = await resp.json();
    showToast(`Record #${createdRecord.id} successfully saved to PostgreSQL!`, "success");

    renderRecordPreview(createdRecord);
    loadSavedRecords(1); // Refresh records list
  } catch (err) {
    showToast(err.message, "error");
  }
}

function renderRecordPreview(rec) {
  const box = document.getElementById("range-results-preview");
  const title = document.getElementById("preview-title");
  const badge = document.getElementById("preview-record-id");
  const tableBody = document.querySelector("#preview-daily-table tbody");

  title.textContent = `Record Saved: ${rec.location_name} (${rec.date_start} to ${rec.date_end})`;
  badge.textContent = `PostgreSQL ID: #${rec.id}`;

  tableBody.innerHTML = "";
  const daily = rec.daily_records || [];
  daily.forEach((d) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${d.date}</strong></td>
      <td>${d.temp_max !== null ? d.temp_max + " °C" : "--"}</td>
      <td>${d.temp_min !== null ? d.temp_min + " °C" : "--"}</td>
      <td>${d.temp_mean !== null ? d.temp_mean + " °C" : "--"}</td>
      <td>${d.precipitation_sum !== null ? d.precipitation_sum + " mm" : "0 mm"}</td>
      <td>${d.wind_speed_max !== null ? d.wind_speed_max + " km/h" : "--"}</td>
      <td>${d.weather_description || "N/A"}</td>
    `;
    tableBody.appendChild(tr);
  });

  box.classList.remove("hidden");
  updateMap(rec.latitude, rec.longitude, rec.location_name, `Saved Record #${rec.id}`);
}

/* -------------------------------------------------------------------------
   6. CRUD: READ (Paginated Records from PostgreSQL)
-------------------------------------------------------------------------- */
async function loadSavedRecords(page = 1) {
  state.currentPage = page;
  const tbody = document.getElementById("records-table-body");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4">Fetching records from PostgreSQL...</td></tr>`;

  try {
    let url = `/api/weather/records?page=${page}&per_page=${state.perPage}`;
    if (state.filterQuery) {
      url += `&q=${encodeURIComponent(state.filterQuery)}`;
    }

    const resp = await fetch(url);
    if (!resp.ok) throw new Error("Failed to fetch saved weather records.");

    const data = await resp.json();
    state.totalPages = data.total_pages || 1;

    renderRecordsTable(data.items, data.total);
    updatePaginationControls(data.page, data.total_pages, data.total);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">${err.message}</td></tr>`;
  }
}

function renderRecordsTable(records, total) {
  const tbody = document.getElementById("records-table-body");
  tbody.innerHTML = "";

  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No saved weather records found in PostgreSQL. Use the Range Search above to create one.</td></tr>`;
    return;
  }

  records.forEach((rec) => {
    const tr = document.createElement("tr");
    const count = (rec.daily_records || []).length;
    const createdAtStr = rec.created_at ? rec.created_at.substring(0, 10) : "";

    tr.innerHTML = `
      <td><strong>#${rec.id}</strong></td>
      <td><b>${rec.location_name}</b> <small class="text-muted">(${rec.country || "N/A"})</small></td>
      <td>${rec.latitude.toFixed(2)}, ${rec.longitude.toFixed(2)}</td>
      <td>${rec.date_start} &rarr; ${rec.date_end}</td>
      <td><span class="badge">${count} days</span></td>
      <td>${createdAtStr}</td>
      <td class="text-right">
        <button class="btn btn-outline btn-sm btn-action-view" title="View on map" data-id="${rec.id}"><i class="fa-solid fa-eye"></i></button>
        <button class="btn btn-primary btn-sm btn-action-edit" title="Edit record" data-id="${rec.id}"><i class="fa-solid fa-pen"></i></button>
        <button class="btn btn-danger btn-sm btn-action-delete" title="Delete record" data-id="${rec.id}"><i class="fa-solid fa-trash"></i></button>
      </td>
    `;

    // Bind action buttons
    tr.querySelector(".btn-action-view").addEventListener("click", () => {
      updateMap(rec.latitude, rec.longitude, rec.location_name, `Record #${rec.id} (${rec.date_start}..${rec.date_end})`);
      document.getElementById("map-section").scrollIntoView({ behavior: "smooth" });
    });

    tr.querySelector(".btn-action-edit").addEventListener("click", () => {
      openUpdateModal(rec);
    });

    tr.querySelector(".btn-action-delete").addEventListener("click", () => {
      openDeleteModal(rec);
    });

    tbody.appendChild(tr);
  });
}

function updatePaginationControls(page, totalPages, totalCount) {
  const info = document.getElementById("pagination-info");
  const badge = document.getElementById("current-page-badge");
  const prevBtn = document.getElementById("btn-prev-page");
  const nextBtn = document.getElementById("btn-next-page");

  if (info) info.textContent = `Total Saved Records: ${totalCount}`;
  if (badge) badge.textContent = `Page ${page} of ${totalPages}`;
  if (prevBtn) prevBtn.disabled = page <= 1;
  if (nextBtn) nextBtn.disabled = page >= totalPages;
}

/* -------------------------------------------------------------------------
   7. CRUD: UPDATE (Edit Record & Re-fetch Weather)
-------------------------------------------------------------------------- */
function openUpdateModal(rec) {
  document.getElementById("edit-record-id").value = rec.id;
  document.getElementById("edit-location").value = rec.location_name;
  document.getElementById("edit-start-date").value = rec.date_start;
  document.getElementById("edit-end-date").value = rec.date_end;

  document.getElementById("update-modal").classList.remove("hidden");
}

function closeUpdateModal() {
  document.getElementById("update-modal").classList.add("hidden");
}

async function submitRecordUpdate() {
  const id = document.getElementById("edit-record-id").value;
  const location = document.getElementById("edit-location").value.trim();
  const date_start = document.getElementById("edit-start-date").value;
  const date_end = document.getElementById("edit-end-date").value;

  if (date_start > date_end) {
    showToast("Start date cannot be after end date.", "error");
    return;
  }

  try {
    showToast(`Updating record #${id} and re-fetching weather data...`, "info");
    const resp = await fetch(`/api/weather/records/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ location, date_start, date_end }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "Failed to update record.");
    }

    const updated = await resp.json();
    closeUpdateModal();
    showToast(`Record #${id} successfully updated!`, "success");
    loadSavedRecords(state.currentPage);
    updateMap(updated.latitude, updated.longitude, updated.location_name, `Updated Record #${id}`);
  } catch (err) {
    showToast(err.message, "error");
  }
}

/* -------------------------------------------------------------------------
   8. CRUD: DELETE (Remove Record from PostgreSQL)
-------------------------------------------------------------------------- */
function openDeleteModal(rec) {
  state.recordPendingDelete = rec;
  document.getElementById("delete-record-name").textContent = `#${rec.id} (${rec.location_name})`;
  document.getElementById("delete-modal").classList.remove("hidden");
}

function closeDeleteModal() {
  state.recordPendingDelete = null;
  document.getElementById("delete-modal").classList.add("hidden");
}

async function deleteRecord(id) {
  try {
    showToast(`Deleting record #${id}...`, "info");
    const resp = await fetch(`/api/weather/records/${id}`, {
      method: "DELETE",
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "Failed to delete record.");
    }

    closeDeleteModal();
    showToast(`Record #${id} permanently deleted.`, "success");
    loadSavedRecords(state.currentPage);
  } catch (err) {
    showToast(err.message, "error");
  }
}

/* -------------------------------------------------------------------------
   9. External Integrations: YouTube
-------------------------------------------------------------------------- */
async function loadYouTubeVideos(locationName) {
  const container = document.getElementById("videos-grid");
  const fallbackBox = document.getElementById("youtube-fallback-box");
  const fallbackMsg = document.getElementById("youtube-fallback-msg");
  const fallbackBtn = document.getElementById("youtube-fallback-btn");

  try {
    const resp = await fetch(`/api/integrations/youtube?location=${encodeURIComponent(locationName)}`);
    if (!resp.ok) return;

    const data = await resp.json();
    container.innerHTML = "";

    if (data.videos && data.videos.length > 0) {
      fallbackBox.classList.add("hidden");
      data.videos.forEach((v) => {
        const card = document.createElement("div");
        card.className = "video-card";
        card.innerHTML = `
          <img class="video-thumb" src="${v.thumbnail}" alt="${v.title}">
          <div class="video-info">
            <h4 class="video-title">${v.title}</h4>
            <a href="${v.url}" target="_blank" class="btn btn-secondary btn-sm"><i class="fa-brands fa-youtube"></i> Watch on YouTube</a>
          </div>
        `;
        container.appendChild(card);
      });
    } else {
      // Fallback genuine search URL
      container.innerHTML = `<p class="text-muted">YouTube API key not configured or no embeddable videos found.</p>`;
      fallbackMsg.textContent = data.message || "A genuine YouTube search URL is available for this location.";
      fallbackBtn.href = data.search_url;
      fallbackBox.classList.remove("hidden");
    }
  } catch (err) {
    console.warn("YouTube integration error:", err);
  }
}

/* -------------------------------------------------------------------------
   10. System Health Check
-------------------------------------------------------------------------- */
async function checkSystemHealth() {
  const indicator = document.getElementById("system-status-indicator");
  if (!indicator) return;

  try {
    const resp = await fetch("/api/health");
    if (resp.ok) {
      const data = await resp.json();
      const dbStatus = data.database?.status === "connected" ? "PostgreSQL Connected" : "PostgreSQL Ready";
      indicator.innerHTML = `<span class="status-dot"></span> ${dbStatus}`;
    }
  } catch (err) {
    indicator.innerHTML = `<span class="status-dot" style="background:#E53E3E"></span> Offline`;
  }
}

/* -------------------------------------------------------------------------
   11. Toast Notifications
-------------------------------------------------------------------------- */
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  
  let icon = "fa-circle-info";
  if (type === "success") icon = "fa-circle-check";
  if (type === "error") icon = "fa-triangle-exclamation";

  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
