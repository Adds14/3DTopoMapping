document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const form = document.getElementById('topo-form');
    const loadingOverlay = document.getElementById('loading-overlay');
    const progressList = document.getElementById('progress-list');
    const errorToast = document.getElementById('error-toast');
    const toastMessage = document.getElementById('toast-message');
    const controlPanel = document.getElementById('control-panel');
    const collapseBtn = document.getElementById('collapse-btn');
    const expandBtn = document.getElementById('expand-btn');
    const downloadPdfBtn = document.getElementById('download-pdf-btn');
    const clearBtn = document.getElementById('clear-btn');
    const emptyState = document.getElementById('empty-state');
    const infoBar = document.getElementById('info-bar');
    const infoLayer = document.getElementById('info-layer');
    const infoContours = document.getElementById('info-contours');
    const contourSection = document.getElementById('contour-section');
    const contourToggle = document.getElementById('contour-toggle');
    const vizDivider = document.getElementById('viz-divider');
    const vizSection = document.getElementById('viz-section');
    const labelsToggle = document.getElementById('labels-toggle');
    const fontSizeSlider = document.getElementById('font-size-slider');
    const fontSizeVal = document.getElementById('font-size-val');
    const opacitySlider = document.getElementById('opacity-slider');
    const opacityVal = document.getElementById('opacity-val');
    const resetVizBtn = document.getElementById('reset-viz-btn');
    const layerCards = document.querySelectorAll('.layer-card');

    // --- State Variables ---
    let map = null;
    let currentCoords = null;
    let contourLayer = null;
    let fillLayer = null;
    let boundaryRect = null;
    let gridLinesLayer = null;
    let markerA = null;
    let markerB = null;
    let customLegend = null;
    let activeBasemapName = 'streets';

    // --- Basemap Definitions ---
    const basemaps = {
        'satellite': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { attribution: '© Esri', maxZoom: 19 }),
        'terrain': L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', { attribution: '© OpenTopoMap', maxNativeZoom: 17, maxZoom: 19 }),
        'streets': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OSM contributors', maxZoom: 19 })
    };

    // --- Initialize Map ---
    const initMap = () => {
        map = L.map('map', {
            zoomControl: false // We will add it manually to position it
        }).fitWorld();

        // Add zoom control top right
        L.control.zoom({ position: 'topright' }).addTo(map);
        
        // Add Scale Control bottom right
        L.control.scale({position: 'bottomright', metric: true, imperial: false}).addTo(map);

        // Add North Arrow top right
        const northControl = L.control({position: 'topright'});
        northControl.onAdd = function() {
            const div = L.DomUtil.create('div', 'north-arrow-control');
            div.innerHTML = '<strong>N</strong><br>↑';
            return div;
        };
        northControl.addTo(map);

        // Add default basemap
        basemaps[activeBasemapName].addTo(map);
    };

    initMap();

    // --- UI Interactions ---
    
    // Panel Collapse/Expand
    collapseBtn.addEventListener('click', () => {
        controlPanel.classList.add('collapsed');
        expandBtn.classList.remove('hidden');
        setTimeout(() => map.invalidateSize(), 300);
    });
    
    expandBtn.addEventListener('click', () => {
        controlPanel.classList.remove('collapsed');
        expandBtn.classList.add('hidden');
        setTimeout(() => map.invalidateSize(), 300);
    });

    // Clear Button
    clearBtn.addEventListener('click', () => {
        form.reset();
        currentCoords = null;
        emptyState.classList.remove('hidden');
        infoBar.classList.add('hidden');
        contourSection.style.display = 'none';
        downloadPdfBtn.disabled = true;
        
        // Remove map elements
        if (boundaryRect) map.removeLayer(boundaryRect);
        if (gridLinesLayer) map.removeLayer(gridLinesLayer);
        if (contourLayer) map.removeLayer(contourLayer);
        if (fillLayer) map.removeLayer(fillLayer);
        if (markerA) map.removeLayer(markerA);
        if (markerB) map.removeLayer(markerB);
        if (customLegend) map.removeControl(customLegend);
        
        map.fitWorld();
    });

    // Layer Switching
    layerCards.forEach(card => {
        card.addEventListener('click', () => {
            // Update active styling
            layerCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            
            // Switch Leaflet layer
            const newLayerName = card.getAttribute('data-layer');
            map.removeLayer(basemaps[activeBasemapName]);
            basemaps[newLayerName].addTo(map);
            activeBasemapName = newLayerName;

            // Ensure our overlays stay on top
            if (fillLayer) fillLayer.bringToFront();
            if (contourLayer) contourLayer.bringToFront();
            if (boundaryRect) boundaryRect.bringToFront();
            
            // Update info bar
            infoLayer.textContent = `Layer: ${newLayerName.charAt(0).toUpperCase() + newLayerName.slice(1)}`;
        });
    });

    // Contour Toggle
    contourToggle.addEventListener('change', (e) => {
        if (contourLayer) {
            if (e.target.checked) map.addLayer(contourLayer);
            else map.removeLayer(contourLayer);
        }
        infoContours.textContent = e.target.checked ? "Contours: ON" : "Contours: OFF";
    });

    // Visualization Toggles & Sliders
    const updateLabels = () => {
        if (!contourLayer) return;
        const show = labelsToggle.checked;
        const size = fontSizeSlider.value;
        const density = document.querySelector('input[name="density"]:checked').value;
        const step = density === 'high' ? 1 : (density === 'low' ? 3 : 2);
        
        // Update CSS variable for tooltip font size
        document.documentElement.style.setProperty('--label-font-size', `${size}px`);

        contourLayer.eachLayer(layer => {
            const feature = layer.feature;
            if (feature.properties && feature.properties.elevation !== undefined && feature.properties.level_index !== undefined) {
                const is_major = (feature.properties.level_index % step === 0);
                layer.unbindTooltip();
                if (show && is_major) {
                    layer.bindTooltip(`${Math.round(feature.properties.elevation)} m`, {
                        permanent: true, className: "contour-label", direction: "center"
                    });
                }
            }
        });
    };

    labelsToggle.addEventListener('change', updateLabels);
    
    document.querySelectorAll('input[name="density"]').forEach(radio => {
        radio.addEventListener('change', updateLabels);
    });

    fontSizeSlider.addEventListener('input', (e) => {
        fontSizeVal.textContent = `${e.target.value} px`;
        updateLabels();
    });

    opacitySlider.addEventListener('input', (e) => {
        opacityVal.textContent = `${e.target.value}%`;
        if (fillLayer) {
            fillLayer.setOpacity(parseInt(e.target.value) / 100);
        }
    });

    resetVizBtn.addEventListener('click', () => {
        contourToggle.checked = true;
        labelsToggle.checked = true;
        fontSizeSlider.value = 11;
        fontSizeVal.textContent = '11 px';
        opacitySlider.value = 35;
        opacityVal.textContent = '35%';
        document.querySelector('input[name="density"][value="medium"]').checked = true;
        
        if (contourLayer) map.addLayer(contourLayer);
        if (fillLayer) fillLayer.setOpacity(0.35);
        
        infoContours.textContent = "Contours: ON";
        updateLabels();
    });

    // --- Helpers ---
    const showError = (msg) => {
        toastMessage.textContent = msg;
        errorToast.classList.remove('hidden');
        setTimeout(() => errorToast.classList.add('hidden'), 5000);
    };

    const updateLoadingStep = (stepText, status = 'active') => {
        if (status === 'done' && progressList.lastElementChild) {
            progressList.lastElementChild.className = 'done';
            progressList.lastElementChild.innerHTML = `✓ ${progressList.lastElementChild.dataset.text}`;
        }
        
        if (stepText) {
            const li = document.createElement('li');
            li.className = status;
            li.dataset.text = stepText;
            li.innerHTML = status === 'active' ? `○ ${stepText}` : `✓ ${stepText}`;
            progressList.appendChild(li);
        }
    };

    const showLoading = () => {
        progressList.innerHTML = '';
        loadingOverlay.classList.remove('hidden');
    };

    const hideLoading = () => {
        loadingOverlay.classList.add('hidden');
    };

    const buildLegend = (minElev, maxElev) => {
        if (customLegend) map.removeControl(customLegend);
        
        customLegend = L.control({position: 'bottomleft'});
        customLegend.onAdd = function () {
            const div = L.DomUtil.create('div', 'custom-legend');
            
            let html = `<h4>Map Legend</h4>`;
            html += `<div class="legend-item"><span class="legend-color" style="background:#3b82f6; border-radius:50%;"></span> Point A</div>`;
            html += `<div class="legend-item"><span class="legend-color" style="background:#ef4444; border-radius:50%;"></span> Point B</div>`;
            html += `<div class="legend-item"><span class="legend-color" style="border: 2px dashed #fff; background:transparent;"></span> Selected Area</div>`;
            html += `<div class="legend-item"><span class="legend-color" style="height:2px; background:#4a2e15; margin-top:5px;"></span> Topo Contour</div>`;
            
            if (minElev !== undefined) {
                html += `<div style="margin-top: 12px; font-size: 0.75rem; color: var(--text-muted);">Elevation (m)</div>`;
                html += `
                    <div style="width: 100%; height: 12px; background: linear-gradient(to right, #333399, #33ccff, #33cc33, #ffcc66, #996633, #ffffff); border-radius: 2px; margin: 4px 0;"></div>
                    <div style="display: flex; justify-content: space-between; font-size: 10px;">
                        <span>${Math.round(minElev)}</span>
                        <span>${Math.round(maxElev)}</span>
                    </div>
                `;
            }
            div.innerHTML = html;
            return div;
        };
        customLegend.addTo(map);
    };

    // --- Generate Map ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const lat1 = parseFloat(document.getElementById('lat1').value);
        const lon1 = parseFloat(document.getElementById('lon1').value);
        const lat2 = parseFloat(document.getElementById('lat2').value);
        const lon2 = parseFloat(document.getElementById('lon2').value);

        if (isNaN(lat1) || isNaN(lon1) || isNaN(lat2) || isNaN(lon2)) {
            showError("Please enter all four coordinate values.");
            return;
        }

        currentCoords = { lat1, lon1, lat2, lon2 };

        showLoading();
        updateLoadingStep("Validating coordinates", "active");

        try {
            // Clean up old layers
            if (boundaryRect) map.removeLayer(boundaryRect);
            if (gridLinesLayer) map.removeLayer(gridLinesLayer);
            if (contourLayer) map.removeLayer(contourLayer);
            if (fillLayer) map.removeLayer(fillLayer);
            if (markerA) map.removeLayer(markerA);
            if (markerB) map.removeLayer(markerB);

            // Fetch data
            updateLoadingStep(null, "done");
            updateLoadingStep("Processing Earth Engine elevation data", "active");
            const payload = {
                ...currentCoords,
                label_fontsize: parseInt(fontSizeSlider.value),
                color_opacity: parseInt(opacitySlider.value),
                show_labels: labelsToggle.checked,
                show_contours: contourToggle.checked,
                label_density: document.querySelector('input[name="density"]:checked').value
            };
            
            const response = await fetch('/api/contours', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                let errMsg = `Server error: ${response.status}`;
                if (data && data.detail) {
                    if (Array.isArray(data.detail)) {
                        errMsg = data.detail.map(err => err.msg || JSON.stringify(err)).join(' | ');
                    } else if (typeof data.detail === 'string') {
                        errMsg = data.detail;
                    } else {
                        errMsg = JSON.stringify(data.detail);
                    }
                }
                throw new Error(errMsg);
            }

            updateLoadingStep(null, "done");
            updateLoadingStep("Generating vector contours & shading", "active");

            const data = await response.json();
            
            updateLoadingStep(null, "done");
            updateLoadingStep("Rendering GIS workspace", "active");

            const north = Math.max(lat1, lat2);
            const south = Math.min(lat1, lat2);
            const east = Math.max(lon1, lon2);
            const west = Math.min(lon1, lon2);
            const bounds = [[south, west], [north, east]];

            // Setup bounds
            map.setMaxBounds(bounds);
            map.fitBounds(bounds);

            // Add markers
            const aIcon = L.divIcon({className: 'marker-icon marker-a', iconSize: [16,16]});
            const bIcon = L.divIcon({className: 'marker-icon marker-b', iconSize: [16,16]});
            markerA = L.marker([lat1, lon1], {icon: aIcon}).addTo(map);
            markerB = L.marker([lat2, lon2], {icon: bIcon}).addTo(map);

            // Boundary & Grid
            const gridFeatures = [
                L.rectangle(bounds, { color: "#ffffff", weight: 2, fill: false, dashArray: '5, 5' })
            ];
            const latStep = (north - south) / 3;
            const lonStep = (east - west) / 3;
            for (let i = 1; i < 3; i++) {
                gridFeatures.push(L.polyline([[south + (latStep * i), west], [south + (latStep * i), east]], { color: "#ffffff", weight: 1.5, dashArray: '5, 5', opacity: 0.6 }));
                gridFeatures.push(L.polyline([[south, west + (lonStep * i)], [north, west + (lonStep * i)]], { color: "#ffffff", weight: 1.5, dashArray: '5, 5', opacity: 0.6 }));
            }
            gridLinesLayer = L.featureGroup(gridFeatures).addTo(map);

            // Elevation Data processing
            let minElev = Infinity, maxElev = -Infinity;
            if (data.geojson && data.geojson.features) {
                data.geojson.features.forEach(f => {
                    if (f.properties && f.properties.elevation !== undefined) {
                        minElev = Math.min(minElev, f.properties.elevation);
                        maxElev = Math.max(maxElev, f.properties.elevation);
                    }
                });
            }
            if (minElev === Infinity) { minElev = 0; maxElev = 100; }
            if (minElev === maxElev) { maxElev += 1; }

            // Fill Overlay
            if (data.image) {
                fillLayer = L.imageOverlay(`data:image/png;base64,${data.image}`, bounds).addTo(map);
            }

            // Vector Contours
            if (data.geojson && data.geojson.features) {
                contourLayer = L.geoJSON(data.geojson, {
                    style: { color: "#4a2e15", weight: 1.5, opacity: 0.9 }
                }).addTo(map);
            }

            buildLegend(minElev, maxElev);
            updateLabels();

            // Update UI State
            emptyState.classList.add('hidden');
            infoBar.classList.remove('hidden');
            contourSection.style.display = 'block';
            vizDivider.style.display = 'block';
            vizSection.style.display = 'block';
            
            // Sync toggles with current slider values if needed, but defaults are fine
            if (contourToggle.checked && contourLayer) map.addLayer(contourLayer);
            if (!contourToggle.checked && contourLayer) map.removeLayer(contourLayer);
            
            downloadPdfBtn.disabled = false;
            
            updateLoadingStep(null, "done");
            
            // Auto-collapse panel on mobile after generation
            if (window.innerWidth <= 768) {
                controlPanel.classList.add('collapsed');
                expandBtn.classList.remove('hidden');
                setTimeout(() => map.invalidateSize(), 300);
            }

        } catch (error) {
            console.error('Error:', error);
            showError(error.message || "Failed to load map data.");
            updateLoadingStep(error.message, "error");
        } finally {
            setTimeout(() => hideLoading(), 500); // slight delay for visual completion
        }
    });

    // --- Export PDF ---
    downloadPdfBtn.addEventListener('click', async () => {
        if (!currentCoords || downloadPdfBtn.disabled) return;

        showLoading();
        updateLoadingStep("Preparing A4 Landscape PDF", "active");
        
        try {
            const payload = {
                ...currentCoords,
                label_fontsize: parseInt(fontSizeSlider.value),
                color_opacity: parseInt(opacitySlider.value),
                show_labels: labelsToggle.checked,
                show_contours: contourToggle.checked,
                label_density: document.querySelector('input[name="density"]:checked').value
            };

            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                let errMsg = `Server error: ${response.status}`;
                if (data && data.detail) {
                    if (Array.isArray(data.detail)) {
                        errMsg = data.detail.map(err => err.msg || JSON.stringify(err)).join(' | ');
                    } else if (typeof data.detail === 'string') {
                        errMsg = data.detail;
                    } else {
                        errMsg = JSON.stringify(data.detail);
                    }
                }
                throw new Error(errMsg);
            }

            updateLoadingStep(null, "done");
            updateLoadingStep("Downloading file", "active");

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'topographic_map.pdf';
            
            document.body.appendChild(a);
            a.click();
            
            window.URL.revokeObjectURL(url);
            a.remove();
            
            updateLoadingStep(null, "done");
        } catch (error) {
            console.error('Error generating PDF:', error);
            showError(error.message || "Failed to generate PDF.");
        } finally {
            setTimeout(() => hideLoading(), 500);
        }
    });
});
