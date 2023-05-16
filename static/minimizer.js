document.addEventListener('DOMContentLoaded', () => {
  const tableContainer = document.querySelector('.history-table-container');
  const minimizeBtn = document.querySelector('.history-table-minimize-button');
  const table = tableContainer.querySelector('table');
  const sliderWrapper = document.querySelector('.slider-wrapper');
  const minimizeButton = sliderWrapper.querySelector('.screenshots-min-button');
  const slider = sliderWrapper.querySelector('.slider');

  minimizeBtn.addEventListener('click', () => {
    tableContainer.classList.toggle('minimized');
    if (tableContainer.classList.contains('minimized')) {
      minimizeBtn.textContent = '+';
    } else {
      minimizeBtn.textContent = '-';
    }
  });

  table.addEventListener('click', (event) => {
    event.stopPropagation();
  });

  minimizeButton.addEventListener('click', () => {
    sliderWrapper.classList.toggle('minimized');
    if (sliderWrapper.classList.contains('minimized')) {
      minimizeButton.textContent = '+';
      slider.style.display = 'none';
    } else {
      minimizeButton.textContent = '-';
      slider.style.display = 'flex';
    }
  });
});
