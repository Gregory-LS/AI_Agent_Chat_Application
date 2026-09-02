import pytest
from pathlib import Path

def test_css_exists():
    css_path = Path("static/styles.css")
    assert css_path.exists(), "styles.css should exist"

def test_css_has_logout_button_style():
    css_path = Path("static/styles.css")
    content = css_path.read_text()
    # Check that there is a style for the logout button or sidebar footer buttons
    assert "#logout-btn" in content or ".btn-icon" in content or "sidebar-footer" in content, "Should have styles for logout button or sidebar buttons"

def test_css_valid_syntax():
    css_path = Path("static/styles.css")
    content = css_path.read_text()
    # Basic validation: no unclosed braces
    open_braces = content.count('{')
    close_braces = content.count('}')
    assert open_braces == close_braces, f"Mismatched braces: {open_braces} open, {close_braces} close"
