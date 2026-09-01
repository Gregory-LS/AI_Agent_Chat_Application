# Onboarding Wizard - Skills Drawer / Panel

## Overview
This component provides a sliding drawer/panel for selecting starter skills during the onboarding wizard. It includes six pre-defined starter skills: Python, JavaScript, SQL, Git, Docker, Kubernetes. Each skill is displayed as a card with an icon and name. Users can toggle skills on/off and confirm their selection.

## Files
- **src/components/SkillsDrawer.vue** - The drawer component. Accepts `isOpen` prop, emits `close` and `update:selection`.
- **src/components/SkillsDrawer.css** - Styles for the drawer overlay, animation, skill cards, and buttons.
- **src/stores/skills.js** - Vue reactive store managing selected and confirmed skills.
- **tests/test_skills_store.js** - Unit tests for the skills store.
- **tests/test_SkillsDrawer.vue.js** - Unit tests for the SkillsDrawer component.

## Usage
1. Import `SkillsDrawer` in your parent component.
2. Control visibility via `isOpen` prop.
3. Listen for `close` (when user cancels or closes) and `update:selection` (when user confirms).
4. The store (`useSkillsStore`) can be used elsewhere to access `selectedSkills` and `confirmedSkills`.

## Dependencies
- Vue 3
- Vitest for testing

## Run Tests
```bash
npx vitest run
```
