document.addEventListener('DOMContentLoaded', () => {
    const tableContainer = document.querySelector('.history-table-container');
    const minimizeHistoryButton = document.querySelector('.history-table-minimize-button');
    const table = tableContainer.querySelector('table');
    const sliderWrapper = document.querySelector('.slider-wrapper');
    const minimizeSliderButton = sliderWrapper.querySelector('.screenshots-min-button');
    const slider = sliderWrapper.querySelector('.slider');

    document.addEventListener('stationValue', (event) => {
        const station = event.detail.station;
        if (station === false) {
            minimizeSliderButton.style.display = 'none';
            minimizeHistoryButton.style.display = 'none';
        } else {
            tableContainer.classList.remove('minimized');
            minimizeHistoryButton.textContent = '-';
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
        minimizeHistoryButton.textContent = '+';
        minimizeSliderButton.textContent = '+';
        slider.style.display = 'none';
    }

    // Initial check for station value
    const initialStationValue = true; // Replace with your initial station value
    document.dispatchEvent(new CustomEvent('stationValue', { detail: { station: initialStationValue } }));

    minimizeHistoryButton.addEventListener('click', () => {
        tableContainer.classList.toggle('minimized');
        if (tableContainer.classList.contains('minimized')) {
            minimizeHistoryButton.textContent = '+';
        } else {
            minimizeHistoryButton.textContent = '-';
        }
    });

    table.addEventListener('click', (event) => {
        event.stopPropagation();
    });

    minimizeSliderButton.addEventListener('click', () => {
        sliderWrapper.classList.toggle('minimized');
        if (sliderWrapper.classList.contains('minimized')) {
            minimizeSliderButton.textContent = '+';
            slider.style.display = 'none';
        } else {
            minimizeSliderButton.textContent = '-';
            slider.style.display = 'flex';
        }
    });
});
