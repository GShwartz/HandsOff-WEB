const tableContainer = document.querySelector('.history-table-container');
const minimizeBtn = document.querySelector('.history-table-minimize-button');
const table = tableContainer.querySelector('table');

minimizeBtn.addEventListener('click', () => {
  tableContainer.classList.toggle('minimized');
});

table.addEventListener('click', (event) => {
  event.stopPropagation();
});

const sliderWrapper = document.querySelector('.slider-wrapper');
const minimizeButton = document.querySelector('.minimize-button');

minimizeButton.addEventListener('click', () => {
    sliderWrapper.classList.toggle('minimized');
});
