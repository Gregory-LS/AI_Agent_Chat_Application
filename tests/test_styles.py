import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest

CSS_PATH = 'static/styles.css'

@pytest.fixture
def css_content():
    with open(CSS_PATH, 'r') as f:
        return f.read()

class TestBasicCSS:
    def test_file_exists(self):
        assert os.path.exists(CSS_PATH)

    def test_has_root_variables(self, css_content):
        assert ':root' in css_content
        assert '--bg-primary' in css_content
        assert '--text-primary' in css_content
        assert '--accent' in css_content

    def test_has_dark_theme(self, css_content):
        assert '[data-theme="dark"]' in css_content

    def test_has_reset(self, css_content):
        assert 'box-sizing: border-box' in css_content
        assert 'margin: 0' in css_content
        assert 'padding: 0' in css_content

    def test_layout_classes(self, css_content):
        assert '.app-layout' in css_content
        assert '.sidebar' in css_content
        assert '.main-content' in css_content
        assert '.messages-container' in css_content
        assert '.composer-container' in css_content

    def test_message_styles(self, css_content):
        assert '.message' in css_content
        assert '.message.user' in css_content
        assert '.message.assistant' in css_content
        assert '.bubble' in css_content

    def test_button_styles(self, css_content):
        assert '.btn' in css_content
        assert '.btn-primary' in css_content
        assert '.btn-icon' in css_content

    def test_drawer_styles(self, css_content):
        assert '.drawer' in css_content
        assert '.drawer.open' in css_content
        assert '.drawer-backdrop' in css_content

    def test_modal_styles(self, css_content):
        assert '.modal-overlay' in css_content
        assert '.modal' in css_content

    def test_form_elements(self, css_content):
        assert 'input[type="text"]' in css_content
        assert 'select' in css_content
        assert 'textarea' in css_content

    def test_skill_item(self, css_content):
        assert '.skill-item' in css_content

    def test_responsive_breakpoint(self, css_content):
        assert '@media (max-width: 768px)' in css_content

    def test_animations(self, css_content):
        assert '@keyframes fadeIn' in css_content
        assert '@keyframes spin' in css_content

    def test_utility_classes(self, css_content):
        assert '.hidden' in css_content
        assert '.flex' in css_content
        assert '.truncate' in css_content

    def test_scrollbar_styling(self, css_content):
        assert '::-webkit-scrollbar' in css_content

    def test_transition_on_body(self, css_content):
        assert 'transition: background' in css_content or 'transition:' in css_content

    def test_composer_textarea(self, css_content):
        assert '.composer textarea' in css_content

    def test_send_button(self, css_content):
        assert '.composer .send-btn' in css_content

    def test_spinner(self, css_content):
        assert '.spinner' in css_content

    def test_theme_toggle(self, css_content):
        assert '.theme-toggle' in css_content

    def test_danger_button(self, css_content):
        assert '.btn-danger' in css_content

    def test_conversation_item_active(self, css_content):
        assert '.conversation-item.active' in css_content

    def test_sidebar_header(self, css_content):
        assert '.sidebar-header' in css_content

    def test_chat_header(self, css_content):
        assert '.chat-header' in css_content

    def test_model_selector(self, css_content):
        assert '.model-selector' in css_content

    def test_header_actions(self, css_content):
        assert '.header-actions' in css_content

    def test_message_actions(self, css_content):
        assert '.message-actions' in css_content

    def test_form_group(self, css_content):
        assert '.form-group' in css_content

    def test_modal_actions(self, css_content):
        assert '.modal-actions' in css_content

    def test_drawer_header(self, css_content):
        assert '.drawer-header' in css_content

    def test_drawer_body(self, css_content):
        assert '.drawer-body' in css_content

    def test_skill_info(self, css_content):
        assert '.skill-info' in css_content

    def test_sidebar_search(self, css_content):
        assert '.sidebar-search' in css_content

    def test_conversation_list(self, css_content):
        assert '.conversation-list' in css_content

    def test_conversation_item(self, css_content):
        assert '.conversation-item' in css_content

    def test_delete_button(self, css_content):
        assert '.delete-btn' in css_content

    def test_avatar_styles(self, css_content):
        assert '.avatar' in css_content

    def test_font_family_variables(self, css_content):
        assert '--font-sans' in css_content
        assert '--font-mono' in css_content

    def test_shadow_variables(self, css_content):
        assert '--shadow' in css_content
        assert '--shadow-lg' in css_content

    def test_radius_variables(self, css_content):
        assert '--radius' in css_content
        assert '--radius-lg' in css_content

    def test_transition_variable(self, css_content):
        assert '--transition' in css_content

    def test_sidebar_width_variable(self, css_content):
        assert '--sidebar-width' in css_content

    def test_drawer_width_variable(self, css_content):
        assert '--drawer-width' in css_content

    def test_header_height_variable(self, css_content):
        assert '--header-height' in css_content

    def test_accent_light_variable(self, css_content):
        assert '--accent-light' in css_content

    def test_danger_hover(self, css_content):
        assert '--danger-hover' in css_content

    def test_success_variable(self, css_content):
        assert '--success' in css_content

    def test_warning_variable(self, css_content):
        assert '--warning' in css_content

    def test_bg_hover_variable(self, css_content):
        assert '--bg-hover' in css_content

    def test_bg_active_variable(self, css_content):
        assert '--bg-active' in css_content

    def test_border_color_variable(self, css_content):
        assert '--border-color' in css_content

    def test_accent_hover_variable(self, css_content):
        assert '--accent-hover' in css_content

    def test_dark_theme_variables(self, css_content):
        # Check that dark theme overrides exist
        dark_section = css_content.split('[data-theme="dark"]')[1] if '[data-theme="dark"]' in css_content else ''
        assert '--bg-primary' in dark_section
        assert '--text-primary' in dark_section
