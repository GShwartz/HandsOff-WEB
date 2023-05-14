const sliderWrapper = document.querySelector('.slider-wrapper');
const minimizeButton = document.querySelector('.minimize-button');

minimizeButton.addEventListener('click', () => {
    sliderWrapper.classList.toggle('minimized');
});