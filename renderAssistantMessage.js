// renderAssistantMessage.js
// Utility to render markdown with syntax highlighting for assistant messages.
// Assumes `marked` and `hljs` are available globally (e.g., from CDN).

(function() {
  'use strict';

  /**
   * Renders a markdown string into HTML with syntax-highlighted code blocks.
   * @param {string} markdown - The markdown text to render.
   * @returns {string} HTML string.
   */
  function renderAssistantMessage(markdown) {
    if (typeof marked === 'undefined' || typeof hljs === 'undefined') {
      console.error('renderAssistantMessage: marked or hljs not loaded.');
      return markdown; // fallback
    }

    // Configure marked to use highlight.js
    marked.setOptions({
      highlight: function(code, lang) {
        if (lang && hljs.getLanguage(lang)) {
          try {
            return hljs.highlight(code, { language: lang }).value;
          } catch (e) {
            console.warn('Highlighting failed for language:', lang, e);
          }
        }
        // Fallback to auto-detection
        try {
          return hljs.highlightAuto(code).value;
        } catch (e) {
          return code; // return plain text if highlighting fails
        }
      }
    });

    return marked(markdown);
  }

  // Export for various environments
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = renderAssistantMessage;
  } else if (typeof window !== 'undefined') {
    window.renderAssistantMessage = renderAssistantMessage;
  }
})();
