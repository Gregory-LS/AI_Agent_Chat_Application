# Skills Management System

This module provides a simple skills management system with two classes:

- `Skill`: Represents an individual skill with a name, category, and proficiency level (0-100).
- `SkillManager`: Manages a collection of `Skill` objects, allowing add, remove, update, and list operations.

## Usage

```python
from skills import Skill, SkillManager

# Create a skill
skill = Skill("Python", "Programming", 80)

# Create a manager
mgr = SkillManager()

# Add skill
mgr.add(skill)

# List all skills
print(mgr.list_all())

# List by category
print(mgr.list_by_category("Programming"))

# Update proficiency
mgr.update("Python", 90)

# Remove skill
mgr.remove("Python")
```

## Running Tests

```bash
pytest tests/test_skills.py
```
