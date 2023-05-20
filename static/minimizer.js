document.addEventListener('DOMContentLoaded', () => {
  const screenshotHeaderButton = document.getElementById('screenshots-button');
  const slider = document.querySelector('.screenshots-slider');
  const scGrid = document.querySelector('.Screenshots');

  const informationHeaderButton = document.getElementById('information-button');
  const informationContainer = document.querySelector('.information-container');

  const tasksHeaderButton = document.getElementById('tasks-button');
  const tasksContainer = document.querySelector('.tasks-container');

  // Apply minimized effect initially if no row is selected or station is false
  if (!isRowSelected()) {
    scGrid.classList.add('minimized');
    informationContainer.classList.add('minimized');
    tasksContainer.classList.add('minimized');
    slider.style.display = 'none';
  }

  // Initial check for station value
  document.dispatchEvent(new CustomEvent('stationValue', { detail: { station: station } }));

  document.addEventListener('stationValue', (event) => {
    const station = event.detail.station;
    if (station === false) {
      console.log('station:', station);
    } else {
      console.log('station:', station);
    }
  });

  screenshotHeaderButton.addEventListener('click', () => {
    scGrid.classList.toggle('minimized');

    if (scGrid.classList.contains('minimized')) {
      scGrid.style.display = 'none';
    } else {
      screenshotHeaderButton.style.backgroundColor = 'green';
      scGrid.style.display = 'flex';
      slider.style.display = 'flex';
    }

    if (!scGrid.classList.contains('minimized')) {
      informationContainer.classList.add('minimized')
      tasksContainer.classList.add('minimized');
      screenshotHeaderButton.style.backgroundColor = '';
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
