let lastSelectedRow = null;
let station = null;

function setupScript() {
  const rows = document.querySelectorAll(".table-connected-row-data");
  const slider = document.querySelector('.screenshots-slider');
  const sliderNav = document.querySelector('.screenshots-slider-nav');

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
    sliderNav.innerHTML = '';

    for (let i = images.length - 1; i >= 0; i--) {
      const image = images[i];
      const img = document.createElement('img');
      img.src = image.path;
      img.alt = image.alt;
      slider.appendChild(img);

      const navLink = document.createElement('a');
      navLink.href = `#${image.alt}`;
      sliderNav.appendChild(navLink);
    }

    // Display sysinfo files and fetch the content of the newest sysinfo file
    const informationContainer = document.getElementById('information-container');
    informationContainer.innerHTML = '';

    const tasksContainer = document.getElementById('tasks-container');
    tasksContainer.innerHTML = '';

    if (tasksFiles.length > 0) {
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

  function handleRowClick(row) {
    // Deselect all rows and select the clicked one
    rows.forEach(row => {
      row.classList.remove('selected');
    });
    row.classList.add('selected');

    // Get data from selected row
    const [idCell, ipAddressCell, hostnameCell, loggedUserCell, bootTimeCell, connectionTimeCell] = row.cells;
    const selectedRowData = {
      id: idCell.textContent,
      ip_address: ipAddressCell.textContent,
      hostname: hostnameCell.textContent,
      logged_user: loggedUserCell.textContent,
      boot_time: bootTimeCell.textContent,
      connection_time: connectionTimeCell.textContent
    };

    // Fetch images for selected hostname
    if (selectedRowData.hostname.trim() !== '') {
      // Update the heading with the selected hostname
      const screenshotsHeading = document.getElementById('screenshots-button');
      screenshotsHeading.textContent = `Screenshots - ${selectedRowData.hostname.trim()}`;

      const informationHeading = document.getElementById('information-button');
      informationHeading.textContent = `Information - ${selectedRowData.hostname.trim()}`;

      const tasksHeading = document.getElementById('tasks-button');
      tasksHeading.textContent = `Tasks - ${selectedRowData.hostname.trim()}`;

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
          console.log('Row data sent to backend.');
        })
        .catch(error => {
          console.error('Error while sending selected row data to server:', error);
        });

      // Save the last selected row
      lastSelectedRow = row;
    }
  }

  function attachEventListeners() {
    rows.forEach(row => {
      row.addEventListener('click', () => {
        handleRowClick(row);
      });
    });
  }

  attachEventListeners();
}

setupScript();