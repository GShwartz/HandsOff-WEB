const buttonsContainer = document.querySelector('.buttons-container');
buttonsContainer.addEventListener('click', handleButtonClick);

function handleButtonClick(event) {
    const button = event.target.closest('.button');
    if (!button) return;

    const action = button.dataset.action;
    if (action === 'screenshot') {
        makeAjaxRequest(action);
        refreshImageSlider();
  } else {
        makeAjaxRequest(action);
    }
}

function makeAjaxRequest(data) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/controller');
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    xhr.send(JSON.stringify({ data }));
}

function refreshImageSlider() {
    const row = document.querySelector('table tr.row-data');
    const clickEvent = new MouseEvent('click', {
        view: window,
        bubbles: true,
        cancelable: true
    });
    row.dispatchEvent(clickEvent);
};
