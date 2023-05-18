document.addEventListener('DOMContentLoaded', () => {
  const sliderWrapper = document.querySelector('.screenshots-slider-wrapper');
  const slider = sliderWrapper.querySelector('.screenshots-slider');
  const minimizeSliderButton = sliderWrapper.querySelector('.screenshots-minimize-button');

  const informationWrapper = document.querySelector('.information-wrapper');
  const informationContainer = informationWrapper.querySelector('.information-container');
  const minimizeInformationButton = informationWrapper.querySelector('.information-minimize-button');

  const tasksWrapper = document.querySelector('.tasks-wrapper');
  const tasksContainer = tasksWrapper.querySelector('.tasks-container');
  const minimizeTasksButton = tasksWrapper.querySelector('.tasks-minimize-button');

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
      minimizeInformationButton.style.display = 'none';
      minimizeInformationButton.textContent = '+';
      minimizeTasksButton.style.display = 'none';
      minimizeTasksButton.textContent = '+';

    } else {
      minimizeSliderButton.style.display = 'flex';
      minimizeInformationButton.style.display = 'flex';
      minimizeInformationButton.textContent = '-';
      minimizeTasksButton.style.display = 'flex';
      minimizeTasksButton.textContent = '-';
    }

    // Apply minimized effect initially if no row is selected or station is false
    if (!isRowSelected()) {
      sliderWrapper.classList.add('minimized');
      informationContainer.classList.add('minimized');
      tasksContainer.classList.add('minimized');

      minimizeSliderButton.textContent = '+';
      minimizeInformationButton.textContent = '+';
      minimizeTasksButton.textContent = '+';

      slider.style.display = 'none';
    }
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

  minimizeTasksButton.addEventListener('click', () => {
    tasksContainer.classList.toggle('minimized');
    if (tasksContainer.classList.contains('minimized')) {
    minimizeTasksButton.textContent = '+';
    } else {
    minimizeTasksButton.textContent = '-';
    }
    });

});
