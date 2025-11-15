// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search button
    const searchButton = document.querySelector('.btn-outline-secondary');
    if (searchButton) {
        searchButton.addEventListener('click', applySearch);
    }

    // Initialize sort select
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', applySort);
    }

    // Initialize activity buttons
    const activityButtons = document.querySelectorAll('[data-activity-id]');
    activityButtons.forEach(button => {
        button.addEventListener('click', function() {
            viewActivityDetails(this.getAttribute('data-activity-id'));
        });
    });

    // Initialize add activity button
    const addActivityButton = document.querySelector('[data-action="add-activity"]');
    if (addActivityButton) {
        addActivityButton.addEventListener('click', addNewActivity);
    }
});

// Search function
function applySearch() {
    let searchValue = document.getElementById('search-input').value.trim();
    let currentUrl = new URL(window.location.href);

    if (searchValue) {
        currentUrl.searchParams.set('q', searchValue);
    } else {
        currentUrl.searchParams.delete('q');
    }

    window.location.href = currentUrl.toString();
}

// Sort function
function applySort() {
    let sortValue = document.getElementById('sort-select').value;
    let currentUrl = new URL(window.location.href);
    
    if (sortValue) {
        currentUrl.searchParams.set('sort', sortValue);
    } else {
        currentUrl.searchParams.delete('sort');
    }
    
    window.location.href = currentUrl.toString();
}

// View activity details function
function viewActivityDetails(activityId) {
    window.location.href = `/ActDetail/${activityId}/`;
}

// Add new activity function
function addNewActivity() {
    window.location.href = '/add/';
} 