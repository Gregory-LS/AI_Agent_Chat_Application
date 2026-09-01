(() => {
  'use strict';

  const drawer = document.getElementById('skills-drawer');
  const overlay = document.getElementById('drawer-overlay');
  const openButton = document.getElementById('open-drawer');
  const closeButton = document.getElementById('close-drawer');
  const form = document.getElementById('skill-form');
  const skillsList = document.getElementById('skills-list');
  const emptyState = document.getElementById('empty-state');
  const formMessage = document.getElementById('form-message');
  const resetButton = document.getElementById('reset-form');
  const skillIdInput = document.getElementById('skill-id');
  const skillNameInput = document.getElementById('skill-name');
  const skillCategoryInput = document.getElementById('skill-category');
  const skillProficiencyInput = document.getElementById('skill-proficiency');
  const skillDescriptionInput = document.getElementById('skill-description');
  const API_URL = '/api/skills';

  function showMessage(text, isError) {
    formMessage.textContent = text || '';
    formMessage.classList.toggle('error', Boolean(isError));
    if (text) {
      window.setTimeout(() => {
        formMessage.textContent = '';
        formMessage.classList.remove('error');
      }, 3000);
    }
  }

  function openDrawer() {
    drawer.hidden = false;
    overlay.hidden = false;
    document.body.classList.add('drawer-open');
    loadSkills();
  }

  function closeDrawer() {
    drawer.hidden = true;
    overlay.hidden = true;
    document.body.classList.remove('drawer-open');
  }

  openButton.addEventListener('click', openDrawer);
  closeButton.addEventListener('click', closeDrawer);
  overlay.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !drawer.hidden) {
      closeDrawer();
    }
  });

  async function apiRequest(url, options) {
    const config = options || {};
    const response = await fetch(url, {
      method: config.method || 'GET',
      headers: Object.assign({ 'Content-Type': 'application/json' }, config.headers || {}),
      body: config.body || undefined
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || 'Request failed.');
    }
    return data;
  }

  async function loadSkills() {
    try {
      const data = await apiRequest(API_URL);
      renderSkills(data.skills || []);
    } catch (error) {
      showMessage(error.message, true);
    }
  }

  function renderSkills(skills) {
    skillsList.innerHTML = '';
    emptyState.hidden = skills.length > 0;
    skills.forEach((skill) => {
      const item = document.createElement('li');
      item.className = 'skill-item';
      item.dataset.id = skill.id;

      const info = document.createElement('div');
      info.className = 'skill-item__info';

      const name = document.createElement('span');
      name.className = 'skill-item__name';
      name.textContent = skill.name || '';

      const category = document.createElement('span');
      category.className = 'skill-item__category';
      category.textContent = skill.category || 'General';

      const proficiency = Math.max(1, Math.min(5, Number(skill.proficiency) || 1));
      const proficiencyBadge = document.createElement('span');
      proficiencyBadge.className = 'skill-item__proficiency';
      proficiencyBadge.setAttribute('title', proficiency + '/5');
      proficiencyBadge.textContent = '★'.repeat(proficiency) + '☆'.repeat(5 - proficiency);

      info.appendChild(name);
      info.appendChild(category);
      info.appendChild(proficiencyBadge);

      if (skill.description) {
        const description = document.createElement('p');
        description.className = 'skill-item__description';
        description.textContent = skill.description;
        info.appendChild(description);
      }

      const actions = document.createElement('div');
      actions.className = 'skill-item__actions';

      const editButton = document.createElement('button');
      editButton.type = 'button';
      editButton.className = 'btn btn-secondary btn-sm';
      editButton.dataset.action = 'edit';
      editButton.textContent = 'Edit';

      const deleteButton = document.createElement('button');
      deleteButton.type = 'button';
      deleteButton.className = 'btn btn-danger btn-sm';
      deleteButton.dataset.action = 'delete';
      deleteButton.textContent = 'Delete';

      actions.appendChild(editButton);
      actions.appendChild(deleteButton);

      item.appendChild(info);
      item.appendChild(actions);
      skillsList.appendChild(item);
    });
  }

  function populateForm(skill) {
    skillIdInput.value = skill.id || '';
    skillNameInput.value = skill.name || '';
    skillCategoryInput.value = skill.category || '';
    skillProficiencyInput.value = skill.proficiency || 3;
    skillDescriptionInput.value = skill.description || '';
    showMessage('');
  }

  function resetForm() {
    form.reset();
    skillIdInput.value = '';
    skillProficiencyInput.value = '3';
    showMessage('');
  }

  skillsList.addEventListener('click', async (event) => {
    const button = event.target.closest('button[data-action]');
    if (!button) return;
    const item = button.closest('.skill-item');
    const id = item.dataset.id;
    if (button.dataset.action === 'edit') {
      try {
        const data = await apiRequest(API_URL + '/' + encodeURIComponent(id));
        populateForm(data);
      } catch (error) {
        showMessage(error.message, true);
      }
    } else if (button.dataset.action === 'delete') {
      if (!window.confirm('Delete this skill?')) return;
      try {
        await apiRequest(API_URL + '/' + encodeURIComponent(id), { method: 'DELETE' });
        showMessage('Skill deleted.');
        loadSkills();
      } catch (error) {
        showMessage(error.message, true);
      }
    }
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const id = skillIdInput.value;
    const payload = {
      name: skillNameInput.value.trim(),
      category: skillCategoryInput.value.trim(),
      proficiency: Number(skillProficiencyInput.value),
      description: skillDescriptionInput.value.trim()
    };
    try {
      if (id) {
        await apiRequest(API_URL + '/' + encodeURIComponent(id), {
          method: 'PUT',
          body: JSON.stringify(payload)
        });
        showMessage('Skill updated.');
      } else {
        await apiRequest(API_URL, {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        showMessage('Skill added.');
      }
      resetForm();
      loadSkills();
    } catch (error) {
      showMessage(error.message, true);
    }
  });

  resetButton.addEventListener('click', resetForm);
  resetForm();
  loadSkills();
})();
