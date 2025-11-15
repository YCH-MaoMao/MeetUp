    // Form submission handler
document.querySelector('form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // prevent the default form submission behavior
    try {
        const formData = new FormData(this);
        const response = await fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        });

        // check if the response is ok
        if (response.ok) {
            // Redirect to activities page on success
            window.location.href = activitiesUrl;
        } else {
            // Handle error response
            const data = await response.json();
            alert('Error creating activity: ' + (data.message || 'Please try again.'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while creating the activity. Please try again.');
    }
});

// Cancel button
document.getElementById("cancelButton").addEventListener("click", function() {
    window.location.href = activitiesUrl;
});