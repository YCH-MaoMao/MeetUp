
// apply search
function applySearch() {
    let searchValue = document.getElementById('search-input').value.trim();
    let currentUrl = new URL(window.location.href);

    // if search value is not empty, set the search value
    if (searchValue) {
        currentUrl.searchParams.set('q', searchValue);
    } else {
        currentUrl.searchParams.delete('q');
    }

    window.location.href = currentUrl.toString();
}

// apply sort
function applySort() {
    let sortValue = document.getElementById('sort-select').value;
    let currentUrl = new URL(window.location.href);

    // if sort value is not empty, set the sort value
    if (sortValue) {
        currentUrl.searchParams.set('sort', sortValue);
    } else {
        currentUrl.searchParams.delete('sort');
    }
    window.location.href = currentUrl.toString();
}

// load map
document.addEventListener("DOMContentLoaded", function() {
    var fullAddress = activityAddress + ", " + activityZipcode; // 拼接完整地址
    console.log("Fetching coordinates for:", fullAddress);

    // fetch coordinates
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(fullAddress)}`)
        .then(response => response.json())
        .then(data => {
            console.log("Geocoding API Response:", data);

            // if data is not empty, set the coordinates
            if (data.length > 0) {
                var lat = parseFloat(data[0].lat);
                var lon = parseFloat(data[0].lon);

                console.log("Coordinates:", lat, lon);

                // set map view
                var map = L.map('map').setView([lat, lon], 13);

                // add tile layer
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }).addTo(map);

                // add marker
                var marker = L.marker([lat, lon]).addTo(map);
                marker.bindPopup(`<b>${fullAddress}</b>`).openPopup();
            } else {
                console.error("Can‘t find Address");
                alert("Please check your address");
            }
        })
        .catch(error => {
            console.error("Can‘t find Address:", error);
            alert("Address resolution failed, may be limited API request or network problem!");
        });
});
