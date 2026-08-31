// Add regenerate button and fix stop button styling

document.addEventListener('DOMContentLoaded', function() {
  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');
  const chatBox = document.getElementById('chat-box');
  const stopBtn = document.getElementById('stop-btn');
  const regenerateBtn = document.getElementById('regenerate-btn');
  
  // Store the last user message for regeneration
  let lastUserMessage = '';
  
  if (chatForm) {
    chatForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const message = userInput.value.trim();
      if (!message) return;
      
      lastUserMessage = message;
      
      // Add user message to chat box
      const userBubble = document.createElement('div');
      userBubble.className = 'message user-message';
      userBubble.textContent = message;
      chatBox.appendChild(userBubble);
      
      // Clear input
      userInput.value = '';
      
      // Show stop button (and hide regenerate button)
      stopBtn.style.display = 'inline-block';
      regenerateBtn.style.display = 'none';
      
      // Simulate async response (in real app this would be an API call)
      setTimeout(() => {
        const assistantBubble = document.createElement('div');
        assistantBubble.className = 'message assistant-message';
        assistantBubble.textContent = 'This is a simulated response.';
        chatBox.appendChild(assistantBubble);
        
        // Hide stop, show regenerate
        stopBtn.style.display = 'none';
        regenerateBtn.style.display = 'inline-block';
        
        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
      }, 2000);
      
      // Scroll to bottom after adding user message
      chatBox.scrollTop = chatBox.scrollHeight;
    });
  }
  
  // Stop button click – cancel current operation
  if (stopBtn) {
    stopBtn.addEventListener('click', function() {
      stopBtn.style.display = 'none';
      regenerateBtn.style.display = 'inline-block';
      // In real app, cancel the API request
    });
  }
  
  // Regenerate button click – resend last user message
  if (regenerateBtn) {
    regenerateBtn.addEventListener('click', function() {
      if (!lastUserMessage) return;
      
      // Remove the last assistant message if exists
      const messages = chatBox.querySelectorAll('.message');
      if (messages.length > 0) {
        const lastMsg = messages[messages.length - 1];
        if (lastMsg.classList.contains('assistant-message')) {
          lastMsg.remove();
        }
      }
      
      // Show stop button, hide regenerate
      stopBtn.style.display = 'inline-block';
      regenerateBtn.style.display = 'none';
      
      // Simulate async response again
      setTimeout(() => {
        const assistantBubble = document.createElement('div');
        assistantBubble.className = 'message assistant-message';
        assistantBubble.textContent = 'Regenerated response for: ' + lastUserMessage;
        chatBox.appendChild(assistantBubble);
        
        stopBtn.style.display = 'none';
        regenerateBtn.style.display = 'inline-block';
        
        chatBox.scrollTop = chatBox.scrollHeight;
      }, 1500);
    });
  }
});
