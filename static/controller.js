document.addEventListener('DOMContentLoaded', function() {
  const btnsContainer = document.querySelector('.controller-buttons-container');
  btnsContainer.addEventListener('click', handleButtonClick);
  const loadingSpinner = document.querySelector('.loading-spinner');
  loadingSpinner.style.display = 'none';

  const localFilesButton = document.getElementById('local-files-button');
  const localClearButton = document.getElementById('local-clear-button');
  const localViewButton = document.getElementById('local-view-button');
  let localFilesClicked = false;

  const remoteButton = document.getElementById('remote-button');
  const anydeskButton = document.getElementById('anydesk-button');
  const teamviewerButton = document.getElementById('teamviewer-button');
  let remoteButtonClicked = false;

  remoteButton.addEventListener('click', () => {
    if (!lastSelectedRow) {
      console.log('No row selected');
      return;
    }

    anydeskButton.classList.toggle('hidden');
    teamviewerButton.classList.toggle('hidden');

  });

  anydeskButton.addEventListener('click', handleAnyDeskButtonClick);
  teamviewerButton.addEventListener('click', handleTeamViewerButtonClick);

  localFilesButton.addEventListener('click', () => {
    if (!lastSelectedRow) {
      console.log('No row selected');
      return;
    }

    localClearButton.classList.toggle('hidden');
    localViewButton.classList.toggle('hidden');
  });

  localViewButton.addEventListener('click', handleViewButtonClick);
  localClearButton.addEventListener('click', handleClearButtonClick);

  async function handleButtonClick(event) {
    console.log('Button clicked');
    const button = event.target.closest('.button');
    if (!button) return;

    const action = button.dataset.action;
    if (action === 'screenshot') {
      const overlay = document.createElement('div');
      const popup = document.createElement('div');
      popup.classList.add('popup', 'fade-in', 'visible');
      popup.innerHTML = `
        <div class="waviy">
          <span>Grabbing Screenshot...</span>
        </div>
        <div class="popup-loading">
          <div class="loading-spinner"></div>
        </div>`;
      overlay.classList.add('overlay', 'visible');
      document.body.appendChild(overlay);
      document.body.appendChild(popup);

      try {
        overlay.style.display = 'block';
        await makeAjaxRequest(action);
      } catch (error) {
        console.error('Error during AJAX request:', error);
      } finally {
        overlay.remove();
        popup.remove();
        refreshImageSlider();
      }

    } else if (action === 'update') {
      if (!lastSelectedRow) {
        console.log('No row selected');
        return;
      }
      const overlay = document.createElement('div');
      const popup = document.createElement('container');
      popup.classList.add('popup', 'fade-in');
      setTimeout(() => {
        popup.classList.remove('visible');
        void popup.offsetWidth; // Trigger reflow to restart the animation
        popup.classList.add('visible');
      }, 50);
      overlay.classList.add('overlay');
      document.body.appendChild(overlay);
      popup.innerHTML = `
        <h1>Update ${lastSelectedRow.cells[2].innerText}?</h1>
        <div class="popup-buttons">
          <button id="yes-button">Yes</button>
          <button id="no-button">No</button>
        </div>`;
      document.body.appendChild(popup);
      const yesButton = document.getElementById('yes-button');
      const noButton = document.getElementById('no-button');
      yesButton.addEventListener('click', handleUpdateConfirmation);
      noButton.addEventListener('click', () => {
        popup.remove();
        overlay.classList.remove('visible');
        document.body.removeChild(overlay);
      });
    } else if (action === 'sysinfo') {
      const overlay = document.createElement('div');
      const popup = document.createElement('div');
      popup.classList.add('popup', 'fade-in', 'visible');
      popup.innerHTML = `
        <div class="waviy">
          <span>Grabbing sysInfo...</span>
        </div>
        <div class="popup-loading">
          <div class="loading-spinner"></div>
        </div>`;
      overlay.classList.add('overlay', 'visible');
      document.body.appendChild(overlay);
      document.body.appendChild(popup);

      try {
        overlay.style.display = 'block';
        await makeAjaxRequest(action);
      } catch (error) {
        console.error('Error during AJAX request:', error);
      } finally {
        overlay.remove();
        popup.remove();
        refreshImageSlider();
      }
    } else if (action === 'restart') {
      if (!lastSelectedRow) {
        console.log('No row selected');
        return;
      }
      const overlay = document.createElement('div');
      const popup = document.createElement('container');
      popup.classList.add('popup', 'fade-in');
      setTimeout(() => {
        popup.classList.remove('visible');
        void popup.offsetWidth; // Trigger reflow to restart the animation
        popup.classList.add('visible');
      }, 50);
      overlay.classList.add('overlay');
      document.body.appendChild(overlay);
      popup.innerHTML = `
        <h1>Restart ${lastSelectedRow.cells[2].innerText}?</h1>
        <div class="popup-buttons">
          <button id="yes-button">Yes</button>
          <button id="no-button">No</button>
        </div>`;
      document.body.appendChild(popup);
      const yesButton = document.getElementById('yes-button');
      const noButton = document.getElementById('no-button');
      yesButton.addEventListener('click', handleRestartConfirmation);
      noButton.addEventListener('click', () => {
        popup.remove();
        overlay.classList.remove('visible');
        document.body.removeChild(overlay);
      });
    } else if (action === 'tasks') {
      if (!lastSelectedRow) {
        console.log('No row selected');
        return;
      }
      button.removeEventListener('click', handleButtonClick); // Remove event listener from the clicked button
      makeAjaxRequest('tasks');
    } else if (action === 'local') {
      return;
    } else {
      if (localFilesClicked || remoteButtonClicked) {
        // If "Local Files" or remote buttons are clicked, don't send any request
        localFilesClicked = false; // Reset the flag
        remoteButtonClicked = false; // Reset the flag
        remoteButton.style.backgroundColor = "";

        return;
      }
      else {
      }
      makeAjaxRequest(action);
    }
  }

  async function handleViewButtonClick() {
    if (!lastSelectedRow) {
      console.log('No row selected');
      return;
    }

    try {
      await makeAjaxRequest('view'); // Send AJAX request with action 'view'
    } catch (error) {
      console.error('Error during AJAX request:', error);
    }
  }

  function handleClearButtonClick() {
    if (!lastSelectedRow) {
      console.log('No row selected');
      return;
    }

    try {
      makeAjaxRequest('clear_local'); // Send AJAX request with action 'clear_local'
      refreshImageSlider();
    } catch (error) {
      console.error('Error during AJAX request:', error);
    }
  }

  function handleRestartConfirmation() {
    makeAjaxRequest('restart');
    const popup = document.querySelector('.popup');
    popup.remove();
    location.reload();
  }

  function handleUpdateConfirmation() {
    makeAjaxRequest('update');
    const popup = document.querySelector('.popup');
    popup.remove();
    location.reload();
  }

  async function makeAjaxRequest(data) {
    console.log('Request data:', data);
    try {
      const response = await fetch('/controller', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json;charset=UTF-8'
        },
        body: JSON.stringify({ data, station })
      });
      const responseData = await response.json();
      console.log('Received response from Flask backend:', responseData);
      if (data === 'error') {
        console.log('error', data);
      }

      if (responseData.type === 'system' || responseData.type === 'tasks') {
        if (responseData.type === 'system') {
          var fileName = responseData.fileName;
          var fileContent = responseData.fileContent;

          var informationContainer = document.querySelector('.information-container');
          var preElement = document.createElement('pre');
          preElement.textContent = responseData.fileContent;
          informationContainer.appendChild(preElement);
          console.log('responseData', fileName);
        } else if (responseData.type === 'tasks') {
          var fileName = responseData.fileName;
          var fileContent = responseData.fileContent;

          var tasksContainer = document.querySelector('.tasks-container');
          tasksContainer.innerHTML = '';
          var preElement = document.createElement('pre');
          preElement.textContent = responseData.fileContent;
          tasksContainer.appendChild(preElement);

          refreshImageSlider();
          console.log('responseData', fileName);
        } else if (responseData.type === 'error') {
          console.log('error', responseData.error);
        }
      }
    } catch (error) {
      console.error('Error in makeAjaxRequest:', error);
    }
  }

  async function handleAnyDeskButtonClick(event) {
    event.stopPropagation(); // Prevent event bubbling
    console.log('AnyDesk button clicked');
    await makeAjaxRequest('anydesk');
  }

  async function handleTeamViewerButtonClick(event) {
    event.stopPropagation(); // Prevent event bubbling
    console.log('TeamViewer button clicked');
    await makeAjaxRequest('teamviewer');
  }
});
