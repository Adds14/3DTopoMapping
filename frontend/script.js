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
        const lat1 = parseFloat(document.getElementById('lat1').value);
        const lon1 = parseFloat(document.getElementById('lon1').value);
        const lat2 = parseFloat(document.getElementById('lat2').value);
        const lon2 = parseFloat(document.getElementById('lon2').value);

        // Validation
        if (isNaN(lat1) || isNaN(lon1) || isNaN(lat2) || isNaN(lon2)) {
            showError("Please enter all four coordinate values.");
            return;
        }

        if (lat1 < -90 || lat1 > 90 || lat2 < -90 || lat2 > 90) {
            showError("Latitudes must be between -90 and 90 degrees.");
            return;
        }

        if (lon1 < -180 || lon1 > 180 || lon2 < -180 || lon2 > 180) {
            showError("Longitudes must be between -180 and 180 degrees.");
            return;
        }

        if (lat1 === lat2 || lon1 === lon2) {
            showError("The coordinates must form a valid rectangle (cannot be on a single line).");
            return;
        }

        // Show loading state
        loadingOverlay.classList.remove('hidden');
        generateBtn.disabled = true;

        try {
            const response = await fetch('http://localhost:8000/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ lat1, lon1, lat2, lon2 }),
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
