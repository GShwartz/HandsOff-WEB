document.addEventListener('DOMContentLoaded', () => {
  const btnsContainer = document.querySelector('.controller-buttons-container');
  btnsContainer.addEventListener('click', handleButtonClick);

  const tasksBtn = document.getElementById('tasksBtn');
  const inputBox = document.getElementById('inp');
  tasksBtn.addEventListener('click', handleTasksBtnClick);

  async function makeRequest(dataType, requestData) {
    try {
      const response = await fetch('/controller', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ data: dataType, ...requestData })
      });

      if (response.ok) {
        const responseData = await response.json();
        console.log('Received response:', responseData);
        handleResponse(responseData);
      } else {
        console.error('Request failed.');
      }
    } catch (error) {
      console.error('Error in makeRequest:', error);
    }
  }

  function handleButtonClick(event) {
    const button = event.target.closest('.button');
    if (!button) return;

    const action = button.dataset.action;
    if (action === 'screenshot') {
      makeRequest(action);
      refreshImageSlider();
    } else if (action === 'update') {
      if (!lastSelectedRow) {
        console.log('No row selected');
        return;
      }
      showConfirmationPopup(`Update ${lastSelectedRow.cells[2].innerText}?`, handleUpdateConfirmation);
    } else if (action === 'sysinfo') {
      makeRequest('sysinfo');
    } else if (action === 'restart') {
      if (!lastSelectedRow) {
        console.log('No row selected');
        return;
      }
      showConfirmationPopup(`Restart ${lastSelectedRow.cells[2].innerText}?`, handleRestartConfirmation);
    } else if (action === 'tasks') {
      if (!lastSelectedRow) {
        console.log('No row selected');
        return;
      }
      makeRequest('tasks');
    } else {
      makeRequest(action);
    }
  }

  function handleTasksBtnClick() {
    const taskName = inputBox.value.trim();
    if (taskName) {
      makeRequest('kill_task', { taskName });
    } else {
      console.log('No task name provided');
    }
  }

  function handleRestartConfirmation() {
    makeRequest('restart');
    closePopup();
    location.reload();
  }

  function handleUpdateConfirmation() {
    makeRequest('update');
    closePopup();
    location.reload();
  }

  function handleResponse(responseData) {
    const { type, message, fileName, fileContent, error, files } = responseData;

    if (message === 'missing') {
      openInstallPopup();
    } else if (message === 'skipped') {
      closePopup();
    } else if (message === 'local_linux') {
      console.log('Local:', files);
    } else if (type === 'system') {
      displayFileContent(fileName, fileContent, '.information-container');
      refreshImageSlider();
    } else if (type === 'tasks') {
      displayFileContent(fileName, fileContent, '.tasks-container');
    } else if (type === 'error') {
      console.log('Error:', error);
    }
  }

  function makeAjaxRequest(data) {
    return fetch('/controller', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json;charset=UTF-8'
      },
      body: JSON.stringify({ data, station })
    })
      .then(response => {
        if (response.ok) {
          return response.json();
        } else {
          throw new Error('Request failed.');
        }
      })
      .then(responseData => {
        console.log('Received response:', responseData);
        handleResponse(responseData);
      })
      .catch(error => {
        console.error('Error in makeAjaxRequest:', error);
      });
  }

  function openInstallPopup() {
    return new Promise((resolve, reject) => {
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
        <h1>Install Anydesk on ${lastSelectedRow.cells[2].innerText}</h1>
        <form>
          <div class="popup-buttons">
            <button type="button" id="install-button">Install</button>
            <button type="button" id="skip-button">Skip</button>
          </div>
        </form>
      `;
      const installButton = popup.querySelector('#install-button');
      const skipButton = popup.querySelector('#skip-button');
      installButton.addEventListener('click', () => {
        makeAjaxRequest('install_anydesk');
        closePopup();
      });
      skipButton.addEventListener('click', () => {
        makeAjaxRequest('skip_anydesk');
        closePopup();
      });
      document.body.appendChild(popup);
    });
  }

  function displayFileContent(fileName, fileContent, containerSelector) {
    const container = document.querySelector(containerSelector);
    container.innerHTML = '';
    const preElement = document.createElement('pre');
    preElement.textContent = fileContent;
    container.appendChild(preElement);
    console.log('Response Data:', fileName);
  }

  function showConfirmationPopup(message, confirmationCallback) {
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
      <h1>${message}</h1>
      <div class="popup-buttons">
        <button id="yes-button">Yes</button>
        <button id="no-button">No</button>
      </div>`;
    document.body.appendChild(popup);
    const yesButton = document.getElementById('yes-button');
    const noButton = document.getElementById('no-button');
    yesButton.addEventListener('click', confirmationCallback);
    noButton.addEventListener('click', () => {
      closePopup();
    });
  }

  function closePopup() {
    const popup = document.querySelector('.popup');
    popup.remove();
    const overlay = document.querySelector('.overlay');
    overlay.classList.remove('visible');
    document.body.removeChild(overlay);
  }
});
