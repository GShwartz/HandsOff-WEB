const rows = document.querySelectorAll(".row-data");
rows.forEach((row) => {
    row.addEventListener("click", () => {
        rows.forEach((row) => {
            row.classList.remove("selected");
        });
        row.classList.add("selected");

        const selectedRowData = {
            id: row.cells[0].innerText,
            ip_address: row.cells[1].innerText,
            hostname: row.cells[2].innerText,
            logged_user: row.cells[3].innerText,
            boot_time: row.cells[4].innerText,
            connection_time: row.cells[5].innerText
        };

        // Check if hostname is not empty
        if (selectedRowData.hostname.trim() !== '') {
            fetch(`/get_images?directory=static/images/${encodeURIComponent(selectedRowData.hostname.trim())}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Received response from Flask backend:', data);
                // Show the images in the slider
                const sliderHtml = getSliderHtml(data.images);
                $('#slider-container').html(sliderHtml);
            })
            .catch(error => {
                console.error('Error while getting images:', error);
            });
        }

        // Send the selected row data to the Flask backend
        fetch('/shell_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(selectedRowData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Received response from Flask backend:', data);
        })
        .catch(error => {
            console.error('Error while sending selected row data to Flask backend:', error);
        });
    });
});

// Helper function to generate HTML for the slider
function getSliderHtml(images) {
    let sliderHtml = '';
    if (images && images.length > 0) {
        sliderHtml += '<div class="slider-container">';
        images.forEach(function(image) {
            sliderHtml += '<div class="slider">';
            sliderHtml += '<img src="' + image.path + '">';
            sliderHtml += '</div>';
        });
        sliderHtml += '</div>';
    } else {
        sliderHtml += '<p>No images found.</p>';
    }
    return sliderHtml;
}
