const rows = document.querySelectorAll(".row-data");
const slider = document.querySelector('.slider');
const sliderNav = document.querySelector('.slider-nav');
let lastSelectedRow = null;
let station = null;

// Refresh image slider
function refreshImageSlider() {
    if (lastSelectedRow) {
        const clickEvent = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true
        });
        lastSelectedRow.dispatchEvent(clickEvent);
    }
}

fetch('/shell_data', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(station)
})
    .then(response => response.json())
    .then(data => {
        const station = data.station;
        window.station = station;
        console.log('station:', data.station)

        const event = new CustomEvent('stationValue', { detail: { station } });
        document.dispatchEvent(event);
    })
    .catch(error => {
        console.error('Error while sending selected row data to server:', error);
});

// Update image slider
const updateSlider = (images, hostname) => {
    slider.innerHTML = '';
    sliderNav.innerHTML = '';
    for (let i = images.length - 1; i >= 0; i--) {
        const image = images[i];
        const img = document.createElement('img');
        img.src = image.path;
        img.alt = image.alt;
        slider.appendChild(img);

        const navLink = document.createElement('a');
        navLink.href = `#${image.alt}`;
        sliderNav.appendChild(navLink);
    }
}

// Add event listeners to buttons and rows
rows.forEach((row) => {
    row.addEventListener("click", () => {
        // Deselect all rows and select the clicked one
        rows.forEach((row) => {
            row.classList.remove("selected");
        });
        row.classList.add("selected");

        // Get data from selected row
        const [id, ip_address, hostname, logged_user, boot_time, connection_time] = row.cells;
        const selectedRowData = {
            id: id.innerText,
            ip_address: ip_address.innerText,
            hostname: hostname.innerText,
            logged_user: logged_user.innerText,
            boot_time: boot_time.innerText,
            connection_time: connection_time.innerText
        };

        // Fetch images for selected hostname
        if (selectedRowData.hostname.trim() !== '') {
            const hostname = encodeURIComponent(selectedRowData.hostname.trim());
            fetch(`/get_images?directory=static/images/${hostname}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
                .then(response => response.json())
                .then(data => {
                    console.log('Received row response from server:', data);
                    // Update the slider with the new images
                    updateSlider(data.images, hostname);
                })
                .catch(error => {
                    console.error('Error while getting images:', error);
                });

            // Send selected row data to server
            fetch('/shell_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(selectedRowData)
            })
                .then(response => response.json())
                .then(data => {
                    const station = data.station;
                    console.log('row data sent to backend.');
                })
                .catch(error => {
                    console.error('Error while sending selected row data to server:', error);
                });

            // Save last selected row
            lastSelectedRow = row;
        }
    });
});
