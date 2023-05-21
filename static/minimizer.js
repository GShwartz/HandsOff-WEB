document.addEventListener('DOMContentLoaded', () => {
  const screenshotHeaderButton = document.getElementById('screenshots-button');
  const screenshotGrid = document.querySelector('.screenshots-slider-wrapper');

  const informationHeaderButton = document.getElementById('information-button');
  const informationContainer = document.querySelector('.information-container');

  const tasksHeaderButton = document.getElementById('tasks-button');
  const tasksContainer = document.querySelector('.tasks-container');

  // Apply minimized effect initially if no row is selected or station is false
  if (!isRowSelected()) {
//    screenshotGrid.classList.add('minimized');
    informationContainer.classList.add('minimized');
    tasksContainer.classList.add('minimized');
  } else {
    screenshotGrid.style.backgroundColor = 'green'; // Change background color to green
  }

  // Modify screenshotHeaderButton to be green when the app starts
  screenshotHeaderButton.style.backgroundColor = 'green';

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
    screenshotGrid.classList.toggle('minimized');
    screenshotHeaderButton.style.backgroundColor = screenshotGrid.classList.contains('minimized') ? '' : 'green';
    screenshotGrid.style.display = screenshotGrid.classList.contains('minimized') ? 'none' : 'flex';
//    screenshotGrid.style.backgroundColor = isRowSelected() ? 'green' : '';

    informationContainer.classList.add('minimized');
    tasksContainer.classList.add('minimized');
    informationHeaderButton.style.backgroundColor = '';
    tasksHeaderButton.style.backgroundColor = '';
  });

  informationHeaderButton.addEventListener('click', () => {
    informationContainer.classList.toggle('minimized');
    informationHeaderButton.style.backgroundColor = informationContainer.classList.contains('minimized') ? '' : 'green';

    screenshotGrid.classList.add('minimized');
    tasksContainer.classList.add('minimized');
    screenshotGrid.style.display = 'none';

    screenshotHeaderButton.style.backgroundColor = '';
    tasksHeaderButton.style.backgroundColor = '';
  });

  tasksHeaderButton.addEventListener('click', () => {
    tasksContainer.classList.toggle('minimized');
    tasksHeaderButton.style.backgroundColor = tasksContainer.classList.contains('minimized') ? '' : 'green';

    screenshotGrid.classList.add('minimized');
    informationContainer.classList.add('minimized');
    screenshotGrid.style.display = 'none';

    screenshotHeaderButton.style.backgroundColor = '';
    informationHeaderButton.style.backgroundColor = '';
  });
});

// Function to check if any row is selected
function isRowSelected() {
  const selectedRow = document.querySelector('.selected');
  return selectedRow !== null;
}
