'''Tests for the Claude-style static stylesheet.'''

from pathlib import Path

CSS_PATH = Path(__file__).resolve().parent.parent / 'static' / 'styles.css'

EXPECTED_TOKENS = (
    ':root',
    '--claude-bg',
    '--claude-accent',
    '.sidebar',
    '.new-chat-button',
    '.chat-container',
    '.message-bubble',
    '.composer',
    '.composer-inner',
    '@media (max-width: 768px)',
)


def _load_css() -> str:
    '''Return the stylesheet contents as text.'''
    return CSS_PATH.read_text(encoding='utf-8')


def test_stylesheet_exists() -> None:
    '''The static stylesheet must be committed next to the app.'''
    assert CSS_PATH.is_file(), f'Missing CSS file: {CSS_PATH}'


def test_css_braces_are_balanced() -> None:
    '''A malformed stylesheet would break the UI styling.'''
    css = _load_css()
    assert css.count('{') > 0
    assert css.count('{') == css.count('}')


def test_claude_theme_tokens_present() -> None:
    '''All key Claude-style variables/components should be defined.'''
    css = _load_css()
    for token in EXPECTED_TOKENS:
        assert token in css, f'Missing token in stylesheet: {token}'


def test_has_reduced_motion_support() -> None:
    '''Accessible fallback for users who prefer reduced motion.'''
    assert '@media (prefers-reduced-motion: reduce)' in _load_css()
