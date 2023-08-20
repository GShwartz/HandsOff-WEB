/*
    HandsOff
	A C&C for IT Admins
	Copyright (C) 2023 Gil Shwartz

    This work is licensed under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    You should have received a copy of the GNU General Public License along with this work.
    If not, see <https://www.gnu.org/licenses/>.
*/

let lastSelectedRow = null;
let checkedList = new Set();
let checkedItems = new Set();
let headerCheckboxChecked = false;
let clickedRowSelected = false;

document.addEventListener('DOMContentLoaded', function () {
  const connectedStations = document.querySelector('.connectedStations');

  const btnsContainer = document.querySelector('.container');
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

  const headerCheckbox = document.getElementById('header-checkbox');
  const rowCheckboxes = document.querySelectorAll('.table-connected-row-data input[type="checkbox"]');
  const rows = document.querySelectorAll(".table-connected-row-data");

  const informationContainer = document.getElementById('information-container');
  const tasksContainer = document.getElementById('tasks-container');

  const slider = document.querySelector('.screenshots-slider');
  const sliderNav = document.querySelector('.screenshots-slider-nav');

  const modal = document.getElementById('imageModal');
  const modalImg = document.getElementById('modalImage');
  const modalClose = document.querySelector('.close');

  // Refresh image slider
  window.refreshImageSlider = function() {
    if (lastSelectedRow) {
      const clickEvent = new MouseEvent('click', {
        view: window,
        bubbles: true,
        cancelable: true
      });


      lastSelectedRow.dispatchEvent(clickEvent);
    }
  }

  function updateSlider(images, hostname, sysinfoFiles, tasksFiles) {
    // Update the slider with the new images
    slider.innerHTML = '';
    informationContainer.innerHTML = '';
    tasksContainer.innerHTML = '';

    for (let i = images.length - 1; i >= 0; i--) {
      const image = images[i];
      // Create an anchor element
      const imgLink = document.createElement('a');
      imgLink.href = `#${image.alt}`; // This can be adjusted as needed
      // Create an image element
      const img = document.createElement('img');
      img.src = image.path;
      img.alt = image.alt;

      // Append the image to the anchor element
      slider.appendChild(img);

      // Append the anchor element to the slider
      slider.appendChild(imgLink);

      const navLink = document.createElement('a');
      navLink.href = `#${image.alt}`;

      img.addEventListener('click', () => {
            // Open the modal and display the clicked image
            modal.style.display = 'block';
            modalImg.src = img.src;
      })};

    if (tasksFiles.length > 0) {
      tasksContainer.innerHTML = '';

      const newestTasksFile = tasksFiles[tasksFiles.length - 1];
      // Fetch the content of the newest tasks file
      fetch(`/get_file_content?filename=${newestTasksFile}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
        .then(response => response.json())
        .then(data => {
          const tasksFileContent = data.fileContent;
          const tasksFileContentElement = document.createElement('pre');
          tasksFileContentElement.textContent = tasksFileContent;
          tasksContainer.appendChild(tasksFileContentElement);
        })
        .catch(error => {
          console.error('Error while getting file content:', error);
        });
    }

    if (sysinfoFiles.length > 0) {
      informationContainer.innerHTML = '';
      const newestSysinfoFile = sysinfoFiles[sysinfoFiles.length - 1];

      // Fetch the content of the newest sysinfo file
      fetch(`/get_file_content?filename=${newestSysinfoFile}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
        .then(response => response.json())
        .then(data => {
          const fileContent = data.fileContent;
          const fileContentElement = document.createElement('pre');
          fileContentElement.textContent = fileContent;
          informationContainer.appendChild(fileContentElement);
        })
        .catch(error => {
          console.error('Error while getting file content:', error);
        });
    }
  }

  function updateHeaderCheckbox() {
    const allChecked = Array.from(rowCheckboxes).every((checkbox) => checkbox.checked);
    headerCheckbox.checked = allChecked;
  }

  function updateCheckedList(event) {
    const row = event.target.parentElement.parentElement;
    const rowData = {
      id: row.dataset.id,
      ip: row.dataset.ip,
      ident: row.dataset.hostname,
      user: row.dataset.user,
      boot_time: row.dataset.boot,
      connection_time: row.dataset.connection,
    };
    const isChecked = event.target.checked;
    const rowDataJSON = JSON.stringify(rowData); // Convert rowData to JSON string

    if (isChecked) {
      checkedList.add(rowDataJSON);
    } else {
      checkedList.delete(rowDataJSON);
    }

    updateHeaderCheckbox();
    updateCheckedCount();
  }

  function updateCheckedCount() {
    console.log(`Number of checked items: ${checkedList.size}`);
    console.log("Checked items:");
    checkedList.forEach((rowDataJSON) => {
      try {
        const rowData = JSON.parse(rowDataJSON); // Parse JSON string back to object
        console.log(rowData);
      } catch (error) {
        console.error('Error parsing JSON:', error);
      }
    });
  }

  function sendDataToServer(rowData, checked, rload) {
    const url = '/shell_data'; // Adjust the URL accordingly
    const method = 'POST';
    const body = JSON.stringify({
      row: rowData,
      checked: checked
    });

    fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: body,
    })
      .then((response) => response.json())
      .then((data) => {
        console.log('Data sent to server:', data);
      })
      .catch((error) => {
        console.error('Error sending data to server:', error);
      });
  }

  function uncheckAllRowCheckboxes() {
      rowCheckboxes.forEach((checkbox) => {
        checkbox.checked = false;
        const row = checkbox.parentElement.parentElement;
        const rowData = {
          id: row.dataset.id,
          ip: row.dataset.ip,
          ident: row.dataset.hostname,
          user: row.dataset.user,
          boot_time: row.dataset.boot,
          connection_time: row.dataset.connection,
        };
        checkedList.delete(JSON.stringify(rowData)); // Convert rowData to JSON string
        row.classList.remove('selected');
      });
    }

  function checkHeaderCheckbox() {
      if (headerCheckbox.checked) {
          checkedList.clear();
          rowCheckboxes.forEach((checkbox) => {
            checkbox.checked = true;
            const row = checkbox.parentElement.parentElement;
            const rowData = {
              id: row.dataset.id,
              ip: row.dataset.ip,
              ident: row.dataset.hostname,
              user: row.dataset.user,
              boot_time: row.dataset.boot,
              connection_time: row.dataset.connection,
            };
            checkedList.add(JSON.stringify(rowData)); // Convert rowData to JSON string
          });

      } else {
        rowCheckboxes.forEach((checkbox) => {
          checkbox.checked = false;
          const row = checkbox.parentElement.parentElement;
          const rowData = {
            id: row.dataset.id,
            ip: row.dataset.ip,
            ident: row.dataset.hostname,
            user: row.dataset.user,
            os_platform: row.os_platform,
            boot_time: row.dataset.boot,
            connection_time: row.dataset.connection,
          };
          checkedList.delete(JSON.stringify(rowData)); // Convert rowData to JSON string
          row.classList.remove('selected');
        });
        if (lastSelectedRow !== null) {
          lastSelectedRow.classList.add('selected');
        }
      }

      headerCheckboxChecked = headerCheckbox.checked;
      updateCheckedCount();
    }

  function reloadPageViaMessage() {
    fetch('/reload', {
      method: 'POST', // Use the appropriate HTTP method (GET, POST, etc.)
      headers: {
        'Content-Type': 'application/json', // Set the appropriate content type
      },
    })
    .then(() => {
      location.reload();
    })
    .catch((error) => {
      console.error('Error sending reload message:', error);
    });
  }

  function handleRowClick(row) {
    rows.forEach(row => {
      row.classList.remove('selected');
    });
    row.classList.add('selected');

    const sliderContainer = document.getElementById('slider-container');
      sliderContainer.style.display = 'block';

      const tabButtonsHeader = document.getElementById('tab-buttons-header');

      tabButtons.forEach(button => {
        button.style.display = 'block';
      });

    // Get data from selected row
    const [selectCell, idCell, ipAddressCell,
    hostnameCell, loggedUserCell, bootTimeCell, connectionTimeCell] = row.cells;
    const selectedRowData = {
      id: idCell.textContent,
      ip_address: ipAddressCell.textContent,
      hostname: hostnameCell.textContent,
      logged_user: loggedUserCell.textContent,
      boot_time: bootTimeCell.textContent,
      connection_time: connectionTimeCell.textContent
    };

    lastSelectedRow = row;

    if (headerCheckbox.checked) {
      headerCheckboxChecked = true;
    } else {
      const checkbox = lastSelectedRow.querySelector('input[type="checkbox"]');
      headerCheckboxChecked = checkbox.checked;
    }

    // Fetch images for selected hostname
    if (selectedRowData.hostname.trim() !== '') {
      const encodedHostname = encodeURIComponent(selectedRowData.hostname.trim());
      fetch(`/get_images?directory=static/images/${encodedHostname}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
        .then(response => response.json())
        .then(data => {
          console.log('Received row response from server:', data);
          // Update the slider with the new images
          updateSlider(data.images, encodedHostname, data.info, data.tasks);
        })
        .catch(error => {
          console.error('Error while getting images:', error);
        });

      // Send selected row data to the server
      fetch('/shell_data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(selectedRowData)
      })
        .then(response => response.json())
        .then(data => {
          station = data.station;
          const fileNum = data.num_files;
          console.log('Row data sent to backend.');
          console.log('fileNum:', fileNum);

//          const fileNotificationBadge = document.getElementById('file-notification-badge');
//          fileNotificationBadge.textContent = fileNum;
//          fileNotificationBadge.style.display = fileNum > 0 ? 'block' : 'none';

        })
        .catch(error => {
          console.error('Error while sending selected row data to server:', error);
        });

      // Save the last selected row
      lastSelectedRow = row;

    }
  }

  headerCheckbox.addEventListener('change', checkHeaderCheckbox);

  rowCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener('change', (event) => {
      updateHeaderCheckbox();
      updateCheckedList(event);
    });
  });

  rows.forEach(row => {
    row.addEventListener('click', () => {
      handleRowClick(row);
      clickedRowSelected = row.classList.contains('selected'); // Update clickedRowSelected flag
    });
  });

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

  function setupButtonFunctionality() {
    document.getElementById('kill_task_button').addEventListener('click', function() {
      var taskName = document.getElementById('inp').value;

      fetch('/kill_task', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ data: { taskName: taskName } })
      })
      .then(function(response) {
        if (response.ok) {
          document.getElementById('inp').value = '';

          return response.json();
        } else {
          throw new Error('Error: ' + response.status);
        }
      })
      .then(function(data) {
        console.log(data.message); // You can handle the response data here
      })
      .catch(function(error) {
        console.log(error); // Handle any errors that occurred during the request
      });

    });
  }

  async function handleButtonClick(event) {
    const button = event.target.closest('.button');
    console.log('Button clicked:', button);
    if (!button) return;

    const action = button.dataset.action;

    if (action === 'screenshot') {
        const selectedRowCount = checkedList.size;
        if (!clickedRowSelected) {
            console.log('Screenshot Error:', 'No selected row.')
            return;
        }

        if (!lastSelectedRow) {
            console.log('Screenshot Error: Row not selected.')
            return;
        }

            console.log('LAST SELECTED ROW:', lastSelectedRow)
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
              await makeAjaxRequest(action, lastSelectedRow);
            } catch (error) {
              console.error('Error during AJAX request:', error);
            } finally {
              overlay.remove();
              popup.remove();
              refreshImageSlider();
              return;
          }

    } else if (action === 'update') {
      const selectedRowCount = checkedList.size;
      console.log('[UPDATE] rowCount:', selectedRowCount);

      if (selectedRowCount === 0) {
        console.log('Update Error: No selected stations.');
        return;
      }

      if (selectedRowCount === 1) {
        const stationDetails = JSON.parse(Array.from(checkedList)[0]);
        console.log('stationDetails:', stationDetails);
        const confirmationMessage = `Update ${stationDetails.ident} (${stationDetails.ip})?`;

        if (confirm(confirmationMessage)) {
          makeAjaxRequest('update');
          location.reload();
          return;
        } else {
            console.log('Update canceled by user.');
            return;
        }

      } else {
        const confirmationMessage = `Update ${selectedRowCount} stations?`;

        if (confirm(confirmationMessage)) {
          makeAjaxRequest('update');
          location.reload();
          return;
        } else {
            console.log("Update canceled by user.");
            return;
        }
      }

  } else if (action === 'sysinfo') {
      const selectedRowCount = checkedList.size;
      if (!clickedRowSelected) {
            console.log('Sysinfo Error:', 'No selected row.')
            return;
        }

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
        return;
      }
    } else if (action === 'restart') {
          const selectedRowCount = checkedList.size;
          console.log('[RESTART] rowCount:', selectedRowCount);

          if (selectedRowCount === 0) {
            console.log('Restart Error: No selected stations.');
            return;
          }

          if (selectedRowCount === 1) {
            const stationDetails = JSON.parse(Array.from(checkedList)[0]);
            console.log('stationDetails:', stationDetails);
            const confirmationMessage = `Restart ${stationDetails.ident} (${stationDetails.ip})?`;

            if (confirm(confirmationMessage)) {
              makeAjaxRequest('restart');
              location.reload();
              return;
            }

            else {
                console.log('Restart canceled by the user.');
                return;
            }

      } else {
        const confirmationMessage = `Restart ${selectedRowCount} stations?`;

        if (confirm(confirmationMessage)) {
          makeAjaxRequest('restart');
          location.reload();
          return;
        } else {
            console.log('Restart canceled by the user.');
            return;
        }
      }

    } else if (action === 'tasks') {
      if (!clickedRowSelected) {
            console.log('Tasks Error:', 'No selected row.')
            return;
      }

      button.removeEventListener('click', handleButtonClick); // Remove event listener from the clicked button
      makeAjaxRequest('tasks');
      return;

    } else if (action === 'local') {
      return;

    } else {
      }
      makeAjaxRequest(action);
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

  async function makeAjaxRequest(action) {
    var checkedItems = Array.from(checkedList);
    if (checkedItems.length === 0 && lastSelectedRow) {
        const rowData = {
          id: lastSelectedRow.dataset.id,
          ip: lastSelectedRow.dataset.ip,
          ident: lastSelectedRow.dataset.hostname,
          user: lastSelectedRow.dataset.user,
          boot_time: lastSelectedRow.dataset.boot,
          connection_time: lastSelectedRow.dataset.connection,
        };
        checkedItems.push(rowData);
      }

    console.log('SENDING AJAX:', action, checkedItems);
    try {
      const response = await fetch('/controller', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json;charset=UTF-8'
        },
        body: JSON.stringify({ action, checkedItems }) // Include checkedItems in the request body
      });

      const responseData = await response.json();
      console.log('Received response from Flask backend:', responseData);
      if (action === 'error') {
        console.log('error', action);
      }

      if (responseData.type === 'system' || responseData.type === 'tasks') {
        if (responseData.type === 'system') {
          var fileName = responseData.fileName;
          var fileContent = responseData.fileContent;

          var preElement = document.createElement('pre');
          preElement.textContent = responseData.fileContent;
          informationContainer.appendChild(preElement);
          console.log('responseData', fileName);
        } else if (responseData.type === 'tasks') {
          var fileName = responseData.fileName;
          var fileContent = responseData.fileContent;

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
    if (!clickedRowSelected) {
            console.log('Anydesk Error:', 'No selected row.')
            remoteButton.click();
            return;
      }

      if (checkedList.size > 1) {
          console.log('Anydesk Error:', 'Too many checked rows.')
          remoteButton.click();
          return;
      }

    await makeAjaxRequest('anydesk');
    remoteButton.click();
  }

  async function handleTeamViewerButtonClick(event) {
    event.stopPropagation(); // Prevent event bubbling
    console.log('TeamViewer button clicked');
    if (!clickedRowSelected) {
            console.log('TeamViewer Error:', 'No selected row.')
            remoteButton.click();
            return;
      }

      if (checkedList.size > 1) {
          console.log('TeamViewer Error:', 'Too many checked rows.')
          remoteButton.click();
          return;
      }

    await makeAjaxRequest('teamviewer');
    remoteButton.click();
  }

// ---------------------------------------------------------------------------------------------------  //
  checkHeaderCheckbox();
  setupButtonFunctionality();

  // Close the modal when the close button is clicked
  modalClose.addEventListener('click', () => {
      modal.style.display = 'none';
  });

  // Close the modal when the user clicks outside the modal
  modal.addEventListener('click', (event) => {
    if (!event.target === modal) {
        modalImg.style.display = 'none';
    }
  });
});