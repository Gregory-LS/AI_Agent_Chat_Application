// composer.js – attachment upload, textarea auto-resize, Ctrl+Enter send

(function() {
    'use strict';

    const fileInput = document.getElementById('fileInput');
    const attachButton = document.querySelector('.attach-button');
    const textarea = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const attachmentPreview = document.getElementById('attachmentPreview');

    // --- Attachment upload ---
    let attachedFiles = [];

    attachButton.addEventListener('click', function() {
        fileInput.click();
    });

    fileInput.addEventListener('change', function() {
        const newFiles = Array.from(fileInput.files);
        attachedFiles = attachedFiles.concat(newFiles);
        renderAttachments();
        fileInput.value = ''; // allow re-uploading same file
    });

    function renderAttachments() {
        attachmentPreview.innerHTML = '';
        attachedFiles.forEach(function(file, index) {
            const div = document.createElement('div');
            div.className = 'attachment-preview';

            const removeBtn = document.createElement('button');
            removeBtn.className = 'remove-attachment';
            removeBtn.textContent = '×';
            removeBtn.addEventListener('click', function() {
                attachedFiles.splice(index, 1);
                renderAttachments();
            });
            div.appendChild(removeBtn);

            if (file.type.startsWith('image/')) {
                const img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                img.alt = file.name;
                div.appendChild(img);
            } else {
                const span = document.createElement('span');
                span.textContent = file.name;
                span.style.fontSize = '14px';
                div.appendChild(span);
            }

            attachmentPreview.appendChild(div);
        });
    }

    // --- Textarea auto-resize ---
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });

    // --- Ctrl+Enter send ---
    textarea.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    sendButton.addEventListener('click', function() {
        sendMessage();
    });

    function sendMessage() {
        const message = textarea.value.trim();
        if (!message && attachedFiles.length === 0) {
            return; // nothing to send
        }

        console.log('Sending message:', message);
        console.log('With attachments:', attachedFiles.map(f => f.name));

        // Clear after send
        textarea.value = '';
        textarea.style.height = 'auto';
        attachedFiles = [];
        renderAttachments();
    }
})();