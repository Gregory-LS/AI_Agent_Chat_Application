'''Tests for the static Claude-style stylesheet.'''

from pathlib import Path


CSS_PATH = Path(__file__).parent.parent / 'static' / 'styles.css'


def read_css() -> str:
    return CSS_PATH.read_text(encoding='utf-8')


def test_css_exists_and_not_empty():
    assert CSS_PATH.is_file()
    assert read_css().strip()


def test_css_braces_balanced():
    css = read_css()
    assert css.count('{') == css.count('}')
    assert css.count('/*') == css.count('*/')


def test_css_has_claude_style_tokens():
    css = read_css()
    assert '--bg: #F5F4EF' in css
    assert '--accent: #D97757' in css
    assert '--surface: #FFFFFF' in css
    assert '--font-display:' in css


def test_css_has_core_ui_components():
    css = read_css()
    selectors = [
        '.card',
        '.btn-primary',
        '.chat',
        '.message-user',
        '.message-assistant',
        '.composer-box',
        '.input',
        '.textarea',
    ]
    for selector in selectors:
        assert selector in css


def test_css_has_responsive_and_reduced_motion_support():
    css = read_css()
    assert '@media (max-width: 640px)' in css
    assert '@media (prefers-reduced-motion: reduce)' in css
