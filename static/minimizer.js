document.addEventListener('DOMContentLoaded', () => {
    const tableContainer = document.querySelector('.history-table-container');
    const minimizeBtn = document.querySelector('.history-table-minimize-button');
    const table = tableContainer.querySelector('table');
    const sliderWrapper = document.querySelector('.slider-wrapper');
    const minimizeButton = sliderWrapper.querySelector('.screenshots-min-button');
    const slider = sliderWrapper.querySelector('.slider');

    document.addEventListener('stationValue', (event) => {
        if (station === false) {
            const minimizeBtn = document.querySelector('.history-table-minimize-button');
            const minimizeButton = document.querySelector('.screenshots-min-button');
            minimizeBtn.click();
            minimizeButton.click();
        }
    });

    // Function to check if any row is selected
    function isRowSelected() {
        const selectedRow = document.querySelector('.selected');
        return selectedRow !== null;
    }

    // Apply minimized effect initially if no row is selected
    if (!isRowSelected()) {
        tableContainer.classList.add('minimized');
        sliderWrapper.classList.add('minimized');
        minimizeBtn.textContent = '+';
        minimizeButton.textContent = '+';
        slider.style.display = 'none';
    }

    minimizeBtn.addEventListener('click', () => {
        tableContainer.classList.toggle('minimized');
        if (tableContainer.classList.contains('minimized')) {
            minimizeBtn.textContent = '+';
        } else {
            minimizeBtn.textContent = '-';
        }
    });

    table.addEventListener('click', (event) => {
        event.stopPropagation();
    });

    minimizeButton.addEventListener('click', () => {
        sliderWrapper.classList.toggle('minimized');
        if (sliderWrapper.classList.contains('minimized')) {
            minimizeButton.textContent = '+';
            slider.style.display = 'none';
        } else {
            minimizeButton.textContent = '-';
            slider.style.display = 'flex';
        }
    });
});
