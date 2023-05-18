document.addEventListener('DOMContentLoaded', () => {
  const screenshotHeaderButton = document.getElementById('screenshots-header');
  const sliderWrapper = document.querySelector('.screenshots-slider-wrapper');
  const slider = sliderWrapper.querySelector('.screenshots-slider');

  const informationHeaderButton = document.getElementById('information-header');
  const informationWrapper = document.querySelector('.information-wrapper');
  const informationContainer = informationWrapper.querySelector('.information-container');

  const tasksHeaderButton = document.getElementById('tasks-header');
  const tasksWrapper = document.querySelector('.tasks-wrapper');
  const tasksContainer = tasksWrapper.querySelector('.tasks-container');
  const minimizeTasksButton = tasksWrapper.querySelector('.tasks-minimize-button');

  // Initial check for station value
  document.dispatchEvent(new CustomEvent('stationValue', { detail: { station: station } }));

  document.addEventListener('stationValue', (event) => {
    const station = event.detail.station;
    if (station === false) {
        console.log('station:', station)

    } else {
        console.log('station:', station)
    }

    // Apply minimized effect initially if no row is selected or station is false
    if (!isRowSelected()) {
      sliderWrapper.classList.add('minimized');
      informationContainer.classList.add('minimized');
      tasksContainer.classList.add('minimized');
      slider.style.display = 'none';
    }
  });

  screenshotHeaderButton.addEventListener('click', () => {
    sliderWrapper.classList.toggle('minimized');
    if (sliderWrapper.classList.contains('minimized')) {
      slider.style.display = 'none';
    } else {
      slider.style.display = 'flex';
    }
  });

  informationHeaderButton.addEventListener('click', () => {
    informationContainer.classList.toggle('minimized');
  });

  tasksHeaderButton.addEventListener('click', () => {
    tasksContainer.classList.toggle('minimized');
  });

});

// Function to check if any row is selected
function isRowSelected() {
const selectedRow = document.querySelector('.selected');
return selectedRow != null;
}