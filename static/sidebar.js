document.addEventListener('DOMContentLoaded', function() {
    const conversationList = document.getElementById('conversation-list');
    const searchInput = document.getElementById('search-input');
    const newConvBtn = document.getElementById('new-conversation-btn');

    // Fetch and render conversations
    function loadConversations(search = '') {
        let url = '/api/conversations';
        if (search) {
            url += `?search=${encodeURIComponent(search)}`;
        }
        fetch(url)
            .then(response => response.json())
            .then(conversations => {
                conversationList.innerHTML = '';
                conversations.forEach(conv => {
                    const li = document.createElement('li');
                    li.className = 'conversation-item';
                    li.dataset.id = conv.id;
                    li.innerHTML = `
                        <div class="conversation-title">${escapeHtml(conv.title)}</div>
                        <div class="conversation-preview">${escapeHtml(conv.last_message)}</div>
                    `;
                    li.addEventListener('click', function() {
                        // Remove active class from all
                        document.querySelectorAll('.conversation-item').forEach(item => item.classList.remove('active'));
                        this.classList.add('active');
                        // Trigger custom event for main content area
                        const event = new CustomEvent('conversationSelected', { detail: { id: conv.id, title: conv.title } });
                        document.dispatchEvent(event);
                    });
                    conversationList.appendChild(li);
                });
            })
            .catch(err => console.error('Failed to load conversations:', err));
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Create new conversation
    function createConversation(title) {
        fetch('/api/conversations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: title })
        })
        .then(response => response.json())
        .then(conv => {
            loadConversations();
            // Optionally select the new conversation
            const items = document.querySelectorAll('.conversation-item');
            items.forEach(item => {
                if (item.dataset.id == conv.id) {
                    item.click();
                }
            });
        })
        .catch(err => console.error('Failed to create conversation:', err));
    }

    // Event listeners
    searchInput.addEventListener('input', function() {
        loadConversations(this.value);
    });

    newConvBtn.addEventListener('click', function() {
        const title = prompt('Enter conversation title:');
        if (title && title.trim()) {
            createConversation(title.trim());
        }
    });

    // Initial load
    loadConversations();
});
