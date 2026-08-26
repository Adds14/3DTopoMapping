document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('topo-form');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    const errorToast = document.getElementById('error-toast');
    const toastMessage = document.getElementById('toast-message');
    const formView = document.getElementById('form-view');
    const dashboardView = document.getElementById('dashboard-view');
    const backBtn = document.getElementById('back-btn');
    const downloadPdfBtn = document.getElementById('download-pdf-btn');
    const mainContainer = document.getElementById('main-container');

    let map = null;
    let currentCoords = null;
    let contourLayer = null;

    // Ripple effect for button
    document.querySelectorAll('.generate-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const x = e.clientX - e.target.getBoundingClientRect().left;
            const y = e.clientY - e.target.getBoundingClientRect().top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });

    const showError = (msg) => {
        toastMessage.textContent = msg;
        errorToast.classList.remove('hidden');
        
        setTimeout(() => {
            errorToast.classList.add('hidden');
        }, 5000);
    };

    const showLoading = (text) => {
        loadingText.textContent = text;
        loadingOverlay.classList.remove('hidden');
    };

    const hideLoading = () => {
        loadingOverlay.classList.add('hidden');
    };

    let fillLayer = null;

    const initMap = (north, south, east, west, data) => {
        const bounds = [
            [south, west],
            [north, east]
        ];

        if (!map) {
            map = L.map('map', {
                maxBounds: bounds,
                maxBoundsViscosity: 1.0
            }).fitBounds(bounds);

            // Basemaps
            const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: '© Esri',
                maxZoom: 19
            });

            const terrain = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenTopoMap',
                maxNativeZoom: 17,
                maxZoom: 19
            });

            const streets = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            });

            satellite.addTo(map);

            const baseMaps = {
                "Satellite": satellite,
                "Terrain": terrain,
                "Streets": streets
            };

            L.control.layers(baseMaps).addTo(map);

            // Add Scale Control
            L.control.scale({position: 'bottomright', metric: true, imperial: false}).addTo(map);

            // Add North Arrow Control
            const northControl = L.control({position: 'topright'});
            northControl.onAdd = function(map) {
                const div = L.DomUtil.create('div', 'north-arrow-control');
                div.innerHTML = '<strong>N</strong><br>↑';
                return div;
            };
            northControl.addTo(map);

        } else {
            map.setMaxBounds(bounds);
            map.fitBounds(bounds);
        }

        if (contourLayer) {
            map.removeLayer(contourLayer);
        }
        
        if (fillLayer) {
            map.removeLayer(fillLayer);
        }

        // Remove old grid lines if any
        if (window.gridLinesLayer) {
            map.removeLayer(window.gridLinesLayer);
        }

        // Draw a boundary rectangle and grid lines
        const gridFeatures = [];
        
        // Add boundary rectangle
        gridFeatures.push(L.rectangle(bounds, {
            color: "#ffffff", 
            weight: 2, 
            fill: false,
            dashArray: '5, 5'
        }));

        // Calculate grid intervals (3 vertical, 3 horizontal lines)
        const latStep = (north - south) / 3;
        const lonStep = (east - west) / 3;

        for (let i = 1; i < 3; i++) {
            // Horizontal lines
            const lat = south + (latStep * i);
            gridFeatures.push(L.polyline([[lat, west], [lat, east]], {
                color: "#ffffff", weight: 1.5, dashArray: '5, 5', opacity: 0.8
            }));
            
            // Vertical lines
            const lon = west + (lonStep * i);
            gridFeatures.push(L.polyline([[south, lon], [north, lon]], {
                color: "#ffffff", weight: 1.5, dashArray: '5, 5', opacity: 0.8
            }));
        }

        window.gridLinesLayer = L.featureGroup(gridFeatures).addTo(map);

        // Add shaded fill overlay
        if (data.image) {
            const imageUrl = `data:image/png;base64,${data.image}`;
            fillLayer = L.imageOverlay(imageUrl, bounds).addTo(map);
        }

        if (data.geojson && data.geojson.features && data.geojson.features.length > 0) {
            const geojson = data.geojson;
            
            // Determine min and max elevation for the legend
            let minElev = Infinity;
            let maxElev = -Infinity;
            geojson.features.forEach(f => {
                if (f.properties && f.properties.elevation !== undefined) {
                    minElev = Math.min(minElev, f.properties.elevation);
                    maxElev = Math.max(maxElev, f.properties.elevation);
                }
            });

            if (minElev === Infinity) { minElev = 0; maxElev = 100; }
            if (minElev === maxElev) { maxElev += 1; }

            contourLayer = L.geoJSON(geojson, {
                style: function (feature) {
                    return {
                        color: "#4a2e15", // Solid brown line
                        weight: 1.5,
                        opacity: 0.9
                    };
                },
                onEachFeature: function (feature, layer) {
                    if (feature.properties && feature.properties.elevation) {
                        layer.bindTooltip(`${Math.round(feature.properties.elevation)} m`, {
                            permanent: true,
                            className: "contour-label",
                            direction: "center"
                        });
                    }
                }
            }).addTo(map);

            // Add Legend Control
            if (window.legendControl) {
                map.removeControl(window.legendControl);
            }

            window.legendControl = L.control({position: 'bottomleft'});
            window.legendControl.onAdd = function (map) {
                const div = L.DomUtil.create('div', 'info legend');
                div.style.background = 'rgba(255, 255, 255, 0.9)';
                div.style.padding = '15px';
                div.style.borderRadius = '4px';
                div.style.border = '2px solid rgba(0, 0, 0, 0.2)';
                div.style.color = '#333';
                div.style.fontFamily = 'Inter, sans-serif';
                div.style.minWidth = '200px';
                
                div.innerHTML = '<h4 style="margin: 0 0 10px 0; font-size: 14px; text-align: center;">Elevation (m)</h4>';
                
                // Create a gradient bar
                div.innerHTML += `
                    <div style="
                        width: 100%;
                        height: 20px;
                        background: linear-gradient(to right, rgb(100, 200, 50), rgb(255, 255, 50), rgb(150, 100, 50), rgb(255, 255, 255));
                        border-radius: 2px;
                        margin-bottom: 8px;
                        border: 1px solid #aaa;
                    "></div>
                `;
                
                div.innerHTML += `
                    <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: bold;">
                        <span>${Math.round(minElev)}</span>
                        <span>${Math.round((minElev + maxElev) / 2)}</span>
                        <span>${Math.round(maxElev)}</span>
                    </div>
                `;
                return div;
            };
            window.legendControl.addTo(map);
        }
    };

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

        showLoading("Generating interactive map data...");

        try {
            const response = await fetch('/api/contours', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentCoords),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || `Server error: ${response.status}`);
            }

            const data = await response.json();
            
            const north = Math.max(lat1, lat2);
            const south = Math.min(lat1, lat2);
            const east = Math.max(lon1, lon2);
            const west = Math.min(lon1, lon2);

            formView.classList.add('hidden');
            dashboardView.classList.remove('hidden');
            mainContainer.style.maxWidth = '1200px';

            initMap(north, south, east, west, data);
            
            // Invalidate size to ensure Leaflet renders correctly after making container visible
            setTimeout(() => {
                map.invalidateSize();
            }, 100);

        } catch (error) {
            console.error('Error fetching contours:', error);
            showError(error.message || "Failed to load map data.");
        } finally {
            hideLoading();
        }
    });

    backBtn.addEventListener('click', () => {
        dashboardView.classList.add('hidden');
        formView.classList.remove('hidden');
        mainContainer.style.maxWidth = '800px';
    });

    downloadPdfBtn.addEventListener('click', async () => {
        if (!currentCoords) return;

        showLoading("Generating high-resolution PDF report...");
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentCoords),
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.detail || `Server error: ${response.status}`);
            }

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
        } catch (error) {
            console.error('Error generating PDF:', error);
            showError(error.message || "Failed to generate PDF.");
        } finally {
            hideLoading();
        }
    });
});
