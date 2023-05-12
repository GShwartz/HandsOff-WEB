let lastSelectedRow = null;
const buttonsContainer = document.querySelector('.buttons-container');
buttonsContainer.addEventListener('click', handleButtonClick);

const slider = document.querySelector('.slider');
const sliderNav = document.querySelector('.slider-nav');
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
            const hostname = encodeURIComponent(selectedRowData.hostname.trim());
            fetch(`/get_images?directory=static/images/${hostname}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Received response from Flask backend:', data);
                // Update the slider with the new images
                updateSlider(data.images, hostname);
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
        lastSelectedRow = row;
    });
});

function handleButtonClick(event) {
    const button = event.target.closest('.button');
    if (!button) return;

    const action = button.dataset.action;
    if (action === 'screenshot') {
        makeAjaxRequest(action);
        refreshImageSlider();
  } else {
        makeAjaxRequest(action);
    }
}

function makeAjaxRequest(data) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/controller');
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    xhr.send(JSON.stringify({ data }));
}

function refreshImageSlider() {
    if (lastSelectedRow) {
        const clickEvent = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true
        });
        lastSelectedRow.dispatchEvent(clickEvent);
    }
};

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
