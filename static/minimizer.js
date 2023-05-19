document.addEventListener('DOMContentLoaded', () => {
  const screenshotHeaderButton = document.getElementById('screenshots-header');
  const sliderWrapper = document.querySelector('.screenshots-slider-wrapper');
  const slider = sliderWrapper.querySelector('.screenshots-slider');
  const scGrid = document.querySelector('.Screenshots');

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
      console.log('station:', station);
    } else {
      console.log('station:', station);
    }

    // Apply minimized effect initially if no row is selected or station is false
    if (!isRowSelected()) {
      scGrid.classList.add('minimized');
      informationContainer.classList.add('minimized');
      tasksContainer.classList.add('minimized');
      slider.style.display = 'none';
    }
  });

  screenshotHeaderButton.addEventListener('click', () => {
    scGrid.classList.toggle('minimized');
    if (scGrid.classList.contains('minimized')) {
      scGrid.style.display = 'none';
    } else {
      scGrid.style.display = 'flex';
      slider.style.display = 'flex';
    }
  });

  informationHeaderButton.addEventListener('click', () => {
    informationContainer.classList.toggle('minimized');
    if (!informationContainer.classList.contains('minimized')) {
      scGrid.classList.add('minimized');
      tasksContainer.classList.add('minimized');
      scGrid.style.display = 'none';
      slider.style.display = 'none';
    }
  });

  tasksHeaderButton.addEventListener('click', () => {
    tasksContainer.classList.toggle('minimized');
    if (!tasksContainer.classList.contains('minimized')) {
      scGrid.classList.add('minimized');
      informationContainer.classList.add('minimized');
      scGrid.style.display = 'none';
      slider.style.display = 'none';
    }
  });
});

// Function to check if any row is selected
function isRowSelected() {
  const selectedRow = document.querySelector('.selected');
  return selectedRow !== null;
}
