document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('topo-form');
    const loadingOverlay = document.getElementById('loading-overlay');
    const errorToast = document.getElementById('error-toast');
    const toastMessage = document.getElementById('toast-message');
    const generateBtn = document.querySelector('.generate-btn');

    // Ripple effect for button
    generateBtn.addEventListener('click', function(e) {
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

    const showError = (msg) => {
        toastMessage.textContent = msg;
        errorToast.classList.remove('hidden');
        
        setTimeout(() => {
            errorToast.classList.add('hidden');
        }, 5000);
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Get values
        const north = parseFloat(document.getElementById('north').value);
        const south = parseFloat(document.getElementById('south').value);
        const east = parseFloat(document.getElementById('east').value);
        const west = parseFloat(document.getElementById('west').value);

        // Validation
        if (isNaN(north) || isNaN(south) || isNaN(east) || isNaN(west)) {
            showError("Please enter all four coordinates.");
            return;
        }

        if (north < -90 || north > 90 || south < -90 || south > 90) {
            showError("Latitude must be between -90 and 90 degrees.");
            return;
        }

        if (east < -180 || east > 180 || west < -180 || west > 180) {
            showError("Longitude must be between -180 and 180 degrees.");
            return;
        }

        if (south >= north) {
            showError("North latitude must be greater than South latitude.");
            return;
        }

        // We allow west > east because it could cross the antimeridian, but for standard maps usually east > west.
        // Assuming standard behavior for now, but keeping it flexible.
        if (west >= east) {
             showError("East longitude must be greater than West longitude.");
             return;
        }

        // Show loading
        loadingOverlay.classList.remove('hidden');

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ north, south, east, west })
            });

            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }

            const blob = await response.blob();
            
            // Trigger download
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
            console.error('Error generating map:', error);
            showError(error.message || "Failed to generate topographic map.");
        } finally {
            // Hide loading
            loadingOverlay.classList.add('hidden');
        }
    });
});
