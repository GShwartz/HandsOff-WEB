const btnsContainer = document.querySelector('.controller-buttons-container');
btnsContainer.addEventListener('click', handleButtonClick);

var confirmationContainer = document.querySelector('.confirmation-container');
var restartButton = document.getElementById('restart');
restartButton.addEventListener('click', function() {
  var buttonRect = restartButton.getBoundingClientRect();
  var top = buttonRect.top + buttonRect.height + 100;
  confirmationContainer.style.display = 'block';
  confirmationContainer.style.top = top + 'px';
});

var cancelButton = document.querySelector('.cancel-button');

cancelButton.addEventListener('click', function() {
  confirmationContainer.style.display = 'none';
});



// Handle button clicks
function handleButtonClick(event) {
    const button = event.target.closest('.button');
    if (!button) return;

    const action = button.dataset.action;
    if (action === 'screenshot') {
        makeAjaxRequest(action);
        refreshImageSlider();

    } else if (action == 'update') {
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


    } else if (action == 'restart') {
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

    } else if (action == 'tasks') {
        if (!lastSelectedRow) {
            console.log('No row selected');
            return;
        }
        makeAjaxRequest('tasks');

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
              <h1>Kill task on ${lastSelectedRow.cells[2].innerText}?</h1>
              <form>
                <label for="task-input">Enter task name (.exe)</label>
                <input type="text" id="task-input" name="task-input">
                <div class="popup-buttons">
                  <button type="button" id="submit-button">Submit</button>
                  <button type="button" id="cancel-button">Cancel</button>
                </div>
              </form>
            `;

            const submitButton = popup.querySelector('#submit-button');
            const cancelButton = popup.querySelector('#cancel-button');
            const taskInput = popup.querySelector('#task-input');

            submitButton.addEventListener('click', () => {
              const taskName = taskInput.value.trim();
              if (taskName) {
                resolve(taskName);
                killTask(taskName);

              } else {
                reject(new Error('No task name provided'));
              }
              popup.remove();
              overlay.classList.remove('visible');
              document.body.removeChild(overlay);
            });

            cancelButton.addEventListener('click', () => {
                const taskName = 'no';
                if (taskName) {
                    resolve(taskName);
                    killTask(taskName);

              } else {
                    reject(new Error('Popup was cancelled'));
              }
                popup.remove();
                overlay.classList.remove('visible');
                document.body.removeChild(overlay);
            });

            document.body.appendChild(popup);
          });
    }
    else {
        makeAjaxRequest(action);
    }
}

function killTask(taskName) {
    // Send taskName data to server
    fetch('/kill_task', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'taskName': taskName })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Received response from server:', data);
    })
    .catch(error => {
        console.error('Error while sending selected row data to server:', error);
    });
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
            popup.remove();
            overlay.classList.remove('visible');
            document.body.removeChild(overlay);
        });
        skipButton.addEventListener('click', () => {
            makeAjaxRequest('skip_anydesk');
            popup.remove();
            overlay.classList.remove('visible');
            document.body.removeChild(overlay);
        });
        document.body.appendChild(popup);

        function closePopup() {
            overlay.classList.remove('visible');
            document.body.removeChild(overlay);
        }

        overlay.classList.add('overlay');
        document.body.appendChild(overlay);

        popup.classList.add('popup', 'fade-in');
        setTimeout(() => {
        popup.classList.remove('visible');
        void popup.offsetWidth; // Trigger reflow to restart the animation
        popup.classList.add('visible');
        }, 50);

        overlay.appendChild(popup);
        });
}

async function makeAjaxRequest(data) {
  try {
    const response = await fetch('/controller', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json;charset=UTF-8'
      },
      body: JSON.stringify({ data })
    });

    const responseData = await response.json();
    console.log('Received response from Flask backend:', responseData);

    if (responseData.message === 'missing') {
      openInstallPopup();
    }

    if (responseData.message === 'skipped') {
      closePopup();
    }

  } catch (error) {
    console.error('Error while sending data to Flask backend:', error);
  }
}
