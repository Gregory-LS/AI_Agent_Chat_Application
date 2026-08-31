// Function to add a message to the chat UI
function addMessage(role, content, metadata) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentSpan = document.createElement('span');
    contentSpan.className = 'message-content';
    contentSpan.innerText = content;
    messageDiv.appendChild(contentSpan);
    
    if (metadata) {
        const metaButton = document.createElement('button');
        metaButton.className = 'meta-toggle';
        metaButton.innerText = 'Show metadata';
        metaButton.onclick = function() {
            const metaDiv = messageDiv.querySelector('.metadata');
            if (metaDiv.style.display === 'none') {
                metaDiv.style.display = 'block';
                metaButton.innerText = 'Hide metadata';
            } else {
                metaDiv.style.display = 'none';
                metaButton.innerText = 'Show metadata';
            }
        };
        messageDiv.appendChild(metaButton);
        
        const metaDiv = document.createElement('div');
        metaDiv.className = 'metadata';
        metaDiv.style.display = 'none';
        metaDiv.innerHTML = `
            <p>Model: ${metadata.model || 'N/A'}</p>
            <p>Latency: ${metadata.latency ? metadata.latency + 's' : 'N/A'}</p>
            <p>Token count: ${metadata.token_count || 'N/A'}</p>
        `;
        messageDiv.appendChild(metaDiv);
    }
    
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Example: sending a message and receiving response with metadata
document.getElementById('send-button').addEventListener('click', async function() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    if (!message) return;
    
    addMessage('user', message, null);
    input.value = '';
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();
        addMessage(data.role, data.content, {
            model: data.model,
            latency: data.latency,
            token_count: data.token_count
        });
    } catch (error) {
        console.error('Error:', error);
        addMessage('assistant', 'Error communicating with server.', null);
    }
});

// Also handle Enter key
document.getElementById('message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        document.getElementById('send-button').click();
    }
});