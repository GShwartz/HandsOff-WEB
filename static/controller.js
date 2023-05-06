  const buttonsContainer = document.querySelector('.buttons-container');
  buttonsContainer.addEventListener('click', handleButtonClick);

  function handleButtonClick(event) {
    const button = event.target.closest('.button');
    if (!button) return;

    const action = button.dataset.action;
    makeAjaxRequest(action);
  }

  function makeAjaxRequest(data) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/controller');
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    xhr.send(JSON.stringify({ data }));
  }