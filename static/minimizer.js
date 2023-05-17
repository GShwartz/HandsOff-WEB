document.addEventListener('DOMContentLoaded', () => {
  const tableContainer = document.querySelector('.history-table-container');
  const minimizeHistoryButton = document.querySelector('.history-minimize-button');
  const table = tableContainer.querySelector('table');

  const sliderWrapper = document.querySelector('.slider-wrapper');
  const minimizeSliderButton = sliderWrapper.querySelector('.screenshots-minimize-button');
  const slider = sliderWrapper.querySelector('.slider');

  const informationWrapper = document.querySelector('.information-wrapper');
  const minimizeInformationButton = informationWrapper.querySelector('.information-minimize-button');
  const informationContainer = informationWrapper.querySelector('.information-container');

  // Initial check for station value
  document.dispatchEvent(new CustomEvent('stationValue', { detail: { station: station } }));

  // Function to check if any row is selected
  function isRowSelected() {
    const selectedRow = document.querySelector('.selected');
    return selectedRow != null;
  }

  document.addEventListener('stationValue', (event) => {
    const station = event.detail.station;
    if (station === false) {
      minimizeSliderButton.style.display = 'none';
      minimizeHistoryButton.style.display = 'none';
      minimizeInformationButton.style.display = 'none';
      minimizeInformationButton.textContent = '+';

    } else {
      minimizeSliderButton.style.display = 'flex';
      minimizeInformationButton.style.display = 'flex';
      minimizeInformationButton.textContent = '-';
    }

    // Apply minimized effect initially if no row is selected or station is false
    if (!isRowSelected()) {
      sliderWrapper.classList.add('minimized');
      informationContainer.classList.add('minimized');

      minimizeSliderButton.textContent = '+';
      minimizeInformationButton.textContent = '+';

      slider.style.display = 'none';
    }
  });

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

  minimizeInformationButton.addEventListener('click', () => {
    informationContainer.classList.toggle('minimized');
    if (informationContainer.classList.contains('minimized')) {
    minimizeInformationButton.textContent = '+';
    } else {
    minimizeInformationButton.textContent = '-';
    }
    });
});
