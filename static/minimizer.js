document.addEventListener('DOMContentLoaded', () => {
  const screenshotHeaderButton = document.getElementById('screenshots-button');
  const screenshotGrid = document.querySelector('.screenshots-slider-wrapper');

  const informationHeaderButton = document.getElementById('information-button');
  const informationContainer = document.querySelector('.information-container');

  const tasksHeaderButton = document.getElementById('tasks-button');
  const tasksContainer = document.querySelector('.tasks-container');

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

  informationHeaderButton.addEventListener('click', () => {
    if (informationHeaderButton.style.backgroundColor !== 'green') {
      informationContainer.classList.toggle('minimized');
      informationHeaderButton.style.backgroundColor = informationContainer.classList.contains('minimized') ? '' : 'green';

      tasksContainer.classList.add('minimized');
      informationContainer.style.height = informationContainer.classList.contains('minimized') ? '20px' : '';

      screenshotHeaderButton.style.backgroundColor = '';
      tasksHeaderButton.style.backgroundColor = '';

      if (informationHeaderButton.style.backgroundColor === 'green') {
        informationHeaderButton.disabled = true;
      } else {
        informationHeaderButton.disabled = false;
      }

      if (tasksHeaderButton.style.backgroundColor === 'green') {
        tasksHeaderButton.disabled = true;
      } else {
        tasksHeaderButton.disabled = false;
      }
    }
  });

  tasksHeaderButton.addEventListener('click', () => {
    if (tasksHeaderButton.style.backgroundColor !== 'green') {
      tasksContainer.classList.toggle('minimized');
      tasksHeaderButton.style.backgroundColor = tasksContainer.classList.contains('minimized') ? '' : 'green';

      informationContainer.classList.add('minimized');
      tasksContainer.style.height = tasksContainer.classList.contains('minimized') ? '20px' : '';

      screenshotHeaderButton.style.backgroundColor = '';
      informationHeaderButton.style.backgroundColor = '';

      if (informationHeaderButton.style.backgroundColor === 'green') {
        informationHeaderButton.disabled = true;
      } else {
        informationHeaderButton.disabled = false;
      }

      if (tasksHeaderButton.style.backgroundColor === 'green') {
        tasksHeaderButton.disabled = true;
      } else {
        tasksHeaderButton.disabled = false;
      }
    }
  });

  // Set initial state for informationContainer and tasksContainer
  informationContainer.classList.remove('minimized');
  informationHeaderButton.style.backgroundColor = 'green';

  tasksContainer.classList.add('minimized');

  // Disable buttons initially if background color is green
  if (informationHeaderButton.style.backgroundColor === 'green') {
    informationHeaderButton.disabled = true;
  }

  if (tasksHeaderButton.style.backgroundColor === 'green') {
    tasksHeaderButton.disabled = true;
  }
});

// Function to check if any row is selected
function isRowSelected() {
  const selectedRow = document.querySelector('.selected');
  return selectedRow !== null;
}
