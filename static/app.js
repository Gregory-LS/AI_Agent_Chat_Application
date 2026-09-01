(function () {
  'use strict';

  var loadButton = document.getElementById('load-btn');
  var itemsList = document.getElementById('items');
  var loadingStatus = document.getElementById('loading-status');
  var toast = document.getElementById('toast');
  var main = document.querySelector('main');
  var toastTimer = null;

  function setLoading(isLoading) {
    loadButton.disabled = isLoading;
    loadingStatus.hidden = !isLoading;
    main.setAttribute('aria-busy', String(isLoading));
  }

  function renderItems(items) {
    itemsList.textContent = '';

    if (!items || items.length === 0) {
      var emptyItem = document.createElement('li');
      emptyItem.className = 'item';
      emptyItem.textContent = 'No tasks found.';
      itemsList.appendChild(emptyItem);
      return;
    }

    var fragment = document.createDocumentFragment();
    items.forEach(function (item) {
      var listItem = document.createElement('li');
      listItem.className = 'item';
      listItem.textContent = item.title;
      fragment.appendChild(listItem);
    });
    itemsList.appendChild(fragment);
  }

  function hideToast() {
    toast.classList.remove('toast--visible');
    toastTimer = null;
    window.setTimeout(function () {
      if (!toast.classList.contains('toast--visible')) {
        toast.hidden = true;
      }
    }, 250);
  }

  function showToast(message) {
    if (toastTimer) {
      window.clearTimeout(toastTimer);
    }
    toast.textContent = message;
    toast.hidden = false;
    requestAnimationFrame(function () {
      toast.classList.add('toast--visible');
    });
    toastTimer = window.setTimeout(hideToast, 5000);
  }

  async function loadTasks() {
    setLoading(true);
    itemsList.textContent = '';

    try {
      var response = await fetch('/api/data', {
        headers: { 'Accept': 'application/json' }
      });

      if (!response.ok) {
        throw new Error('The server could not load your tasks. Please try again.');
      }

      var data = await response.json();
      renderItems(data.items || []);
    } catch (error) {
      showToast(error.message || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  }

  loadButton.addEventListener('click', loadTasks);
})();
