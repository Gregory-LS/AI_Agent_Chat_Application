(function () {
  'use strict';

  const API_BASE = '/api';
  const state = {
    allConversations: [],
    search: '',
    statusFilter: 'all',
    selected: new Set()
  };

  const dom = {
    list: document.getElementById('conversation-list'),
    search: document.getElementById('search-input'),
    filter: document.getElementById('filter-status'),
    selectAll: document.getElementById('select-all'),
    bulkArchive: document.getElementById('bulk-archive'),
    bulkUnarchive: document.getElementById('bulk-unarchive'),
    bulkExport: document.getElementById('bulk-export'),
    bulkDelete: document.getElementById('bulk-delete'),
    exportAll: document.getElementById('export-all'),
    importFile: document.getElementById('import-file'),
    status: document.getElementById('status'),
    empty: document.getElementById('empty-message')
  };

  function setStatus(message, isError) {
    dom.status.textContent = message;
    dom.status.classList.toggle('error', !!isError);
    dom.status.classList.toggle('success', !isError);
  }

  async function api(path, options) {
    const response = await fetch(API_BASE + path, {
      headers: { 'Content-Type': 'application/json' },
      ...(options || {})
    });
    if (!response.ok) {
      let message = 'Request failed';
      try {
        const data = await response.json();
        if (data && data.error) message = data.error;
      } catch (_) {}
      throw new Error(`${response.status} ${message}`);
    }
    if (response.status === 204) return null;
    return response.json();
  }

  async function loadConversations() {
    try {
      const data = await api('/conversations');
      if (Array.isArray(data)) {
        state.allConversations = data;
      } else if (data && Array.isArray(data.conversations)) {
        state.allConversations = data.conversations;
      } else {
        state.allConversations = [];
      }
      state.selected.clear();
      render();
      setStatus(`Loaded ${state.allConversations.length} conversations`);
    } catch (err) {
      setStatus('Error loading conversations: ' + err.message, true);
    }
  }

  function matchesSearch(conv) {
    if (!state.search) return true;
    const query = state.search.toLowerCase();
    return (conv.title || '').toLowerCase().includes(query) ||
           (conv.messages || []).some(msg => (msg.content || '').toLowerCase().includes(query));
  }

  function filteredConversations() {
    let result = state.allConversations.filter(matchesSearch);
    if (state.statusFilter === 'active') {
      result = result.filter(c => !c.archived);
    } else if (state.statusFilter === 'archived') {
      result = result.filter(c => c.archived);
    }
    return result;
  }

  function formatTimestamp(ts) {
    if (!ts) return '—';
    const date = new Date(ts);
    if (isNaN(date.getTime())) return String(ts);
    return date.toLocaleString();
  }

  function render() {
    const items = filteredConversations();
    dom.list.innerHTML = '';
    if (items.length === 0) {
      dom.empty.textContent = state.allConversations.length === 0
        ? 'No conversations yet.'
        : 'No conversations match your filters.';
      dom.empty.hidden = false;
    } else {
      dom.empty.hidden = true;
    }

    for (const conv of items) {
      const tr = document.createElement('tr');
      tr.dataset.id = conv.id;
      tr.classList.toggle('archived', !!conv.archived);

      const checkboxCell = document.createElement('td');
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.className = 'row-check';
      checkbox.checked = state.selected.has(conv.id);
      checkbox.addEventListener('change', () => {
        if (checkbox.checked) state.selected.add(conv.id);
        else state.selected.delete(conv.id);
        updateBulkButtons();
        updateSelectAll();
      });
      checkboxCell.appendChild(checkbox);

      const titleCell = document.createElement('td');
      titleCell.className = 'title-cell';
      titleCell.textContent = conv.title || 'Untitled';

      const updatedCell = document.createElement('td');
      updatedCell.textContent = formatTimestamp(conv.updated_at || conv.updatedAt || conv.created_at);

      const statusCell = document.createElement('td');
      const statusBadge = document.createElement('span');
      statusBadge.className = 'badge ' + (conv.archived ? 'badge-archived' : 'badge-active');
      statusBadge.textContent = conv.archived ? 'Archived' : 'Active';
      statusCell.appendChild(statusBadge);

      const actionsCell = document.createElement('td');
      const actions = document.createElement('div');
      actions.className = 'actions';

      const archiveBtn = document.createElement('button');
      archiveBtn.className = 'btn small';
      archiveBtn.textContent = conv.archived ? 'Unarchive' : 'Archive';
      archiveBtn.addEventListener('click', () => toggleArchive(conv.id, !conv.archived));
      actions.appendChild(archiveBtn);

      const exportBtn = document.createElement('button');
      exportBtn.className = 'btn small';
      exportBtn.textContent = 'Export';
      exportBtn.addEventListener('click', () => exportOne(conv.id));
      actions.appendChild(exportBtn);

      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'btn small danger';
      deleteBtn.textContent = 'Delete';
      deleteBtn.addEventListener('click', () => deleteConversation(conv.id));
      actions.appendChild(deleteBtn);

      actionsCell.appendChild(actions);
      tr.append(checkboxCell, titleCell, updatedCell, statusCell, actionsCell);
      dom.list.appendChild(tr);
    }
    updateBulkButtons();
    updateSelectAll();
  }

  function updateBulkButtons() {
    const count = state.selected.size;
    dom.bulkArchive.disabled = count === 0;
    dom.bulkUnarchive.disabled = count === 0;
    dom.bulkExport.disabled = count === 0;
    dom.bulkDelete.disabled = count === 0;
  }

  function updateSelectAll() {
    const checkboxes = Array.from(document.querySelectorAll('.row-check'));
    const checked = checkboxes.filter(cb => cb.checked).length;
    dom.selectAll.checked = checkboxes.length > 0 && checked === checkboxes.length;
    dom.selectAll.indeterminate = checked > 0 && checked < checkboxes.length;
  }

  async function toggleArchive(id, archived) {
    try {
      await api(`/conversations/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        body: JSON.stringify({ archived })
      });
      const conv = state.allConversations.find(c => c.id === id);
      if (conv) conv.archived = archived;
      render();
      setStatus(`Conversation ${archived ? 'archived' : 'unarchived'}.`);
    } catch (err) {
      setStatus('Error: ' + err.message, true);
    }
  }

  async function deleteConversation(id) {
    if (!confirm('Delete this conversation permanently?')) return;
    try {
      await api(`/conversations/${encodeURIComponent(id)}`, { method: 'DELETE' });
      state.allConversations = state.allConversations.filter(c => c.id !== id);
      state.selected.delete(id);
      render();
      setStatus('Conversation deleted.');
    } catch (err) {
      setStatus('Error: ' + err.message, true);
    }
  }

  async function exportConversations(ids) {
    const selectedIds = ids || state.allConversations.map(c => c.id);
    const conversations = [];
    try {
      for (const id of selectedIds) {
        const conv = await api(`/conversations/${encodeURIComponent(id)}`);
        conversations.push(conv);
      }
      const blob = new Blob([JSON.stringify({ conversations }, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversations-${new Date().toISOString().slice(0,10)}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setStatus(`Exported ${conversations.length} conversation(s).`);
    } catch (err) {
      setStatus('Export failed: ' + err.message, true);
    }
  }

  async function exportAll() {
    await exportConversations();
  }

  async function exportOne(id) {
    await exportConversations([id]);
  }

  async function exportSelected() {
    await exportConversations(Array.from(state.selected));
  }

  async function importFile(file) {
    let parsed;
    try {
      parsed = JSON.parse(await file.text());
    } catch (_) {
      setStatus('Invalid JSON file.', true);
      return;
    }
    const list = parsed.conversations || parsed;
    if (!Array.isArray(list)) {
      setStatus('Import file must contain a "conversations" array.', true);
      return;
    }
    let success = 0;
    let failed = 0;
    for (const conv of list) {
      try {
        await api('/conversations', {
          method: 'POST',
          body: JSON.stringify({
            title: conv.title || 'Imported conversation',
            messages: conv.messages || [],
            archived: !!conv.archived,
            created_at: conv.created_at,
            updated_at: conv.updated_at
          })
        });
        success++;
      } catch (_) {
        failed++;
      }
    }
    setStatus(`Imported ${success} conversation(s)` + (failed ? `, ${failed} failed` : '') + '.');
    await loadConversations();
  }

  dom.search.addEventListener('input', () => {
    state.search = dom.search.value.trim();
    render();
  });

  dom.filter.addEventListener('change', () => {
    state.statusFilter = dom.filter.value;
    render();
  });

  dom.selectAll.addEventListener('change', () => {
    const checkboxes = Array.from(document.querySelectorAll('.row-check'));
    checkboxes.forEach(cb => {
      cb.checked = dom.selectAll.checked;
      if (dom.selectAll.checked) state.selected.add(cb.closest('tr').dataset.id);
      else state.selected.delete(cb.closest('tr').dataset.id);
    });
    updateBulkButtons();
  });

  dom.bulkArchive.addEventListener('click', async () => {
    for (const id of Array.from(state.selected)) {
      try {
        await api(`/conversations/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify({ archived: true }) });
        const conv = state.allConversations.find(c => c.id === id);
        if (conv) conv.archived = true;
      } catch (err) {
        setStatus(`Error archiving ${id}: ${err.message}`, true);
        return;
      }
    }
    state.selected.clear();
    render();
    setStatus('Selected conversations archived.');
  });

  dom.bulkUnarchive.addEventListener('click', async () => {
    for (const id of Array.from(state.selected)) {
      try {
        await api(`/conversations/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify({ archived: false }) });
        const conv = state.allConversations.find(c => c.id === id);
        if (conv) conv.archived = false;
      } catch (err) {
        setStatus(`Error unarchiving ${id}: ${err.message}`, true);
        return;
      }
    }
    state.selected.clear();
    render();
    setStatus('Selected conversations unarchived.');
  });

  dom.bulkExport.addEventListener('click', exportSelected);

  dom.bulkDelete.addEventListener('click', async () => {
    if (!confirm(`Delete ${state.selected.size} selected conversation(s)?`)) return;
    for (const id of Array.from(state.selected)) {
      try {
        await api(`/conversations/${encodeURIComponent(id)}`, { method: 'DELETE' });
        state.allConversations = state.allConversations.filter(c => c.id !== id);
      } catch (err) {
        setStatus(`Error deleting ${id}: ${err.message}`, true);
        return;
      }
    }
    state.selected.clear();
    render();
    setStatus('Selected conversations deleted.');
  });

  dom.exportAll.addEventListener('click', exportAll);

  dom.importFile.addEventListener('change', () => {
    const file = dom.importFile.files[0];
    if (file) importFile(file);
    dom.importFile.value = '';
  });

  loadConversations();
})();
