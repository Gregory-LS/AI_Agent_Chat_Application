import os
import re

STYLES_PATH = os.path.join(os.path.dirname(__file__), '..', 'static', 'styles.css')

def test_styles_exists():
    assert os.path.isfile(STYLES_PATH), "styles.css should exist"

def test_dark_theme_variables():
    with open(STYLES_PATH, 'r') as f:
        content = f.read()
    
    # Check that dark theme section exists
    assert '[data-theme="dark"]' in content, "Dark theme selector should be present"
    
    # Check that key CSS variables are defined for dark theme
    dark_section = re.search(r'\[data-theme="dark"\]\s*\{[^}]+\}', content, re.DOTALL)
    assert dark_section, "Dark theme should have a CSS block"
    
    dark_block = dark_section.group()
    required_vars = [
        '--bg-primary',
        '--bg-secondary',
        '--text-primary',
        '--text-secondary',
        '--accent',
        '--border'
    ]
    for var in required_vars:
        assert var in dark_block, f"Dark theme should define {var}"

def test_light_theme_variables():
    with open(STYLES_PATH, 'r') as f:
        content = f.read()
    
    # Check that :root has light theme variables
    root_section = re.search(r':root\s*\{[^}]+\}', content, re.DOTALL)
    assert root_section, ":root should have a CSS block"
    
    root_block = root_section.group()
    required_vars = [
        '--bg-primary',
        '--bg-secondary',
        '--text-primary',
        '--text-secondary',
        '--accent',
        '--border'
    ]
    for var in required_vars:
        assert var in root_block, f":root should define {var}"

def test_theme_toggle_button_style():
    with open(STYLES_PATH, 'r') as f:
        content = f.read()
    
    assert '#theme-toggle' in content, "Theme toggle button style should be defined"
