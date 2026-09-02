class Skill:
    """Represents a skill with a name, category, and proficiency level."""

    def __init__(self, name: str, category: str, proficiency: int):
        if not isinstance(proficiency, int) or not (0 <= proficiency <= 100):
            raise ValueError("Proficiency must be an integer between 0 and 100")
        self.name = name
        self.category = category
        self.proficiency = proficiency

    def __repr__(self):
        return f"Skill(name={self.name!r}, category={self.category!r}, proficiency={self.proficiency})"

    def __eq__(self, other):
        if not isinstance(other, Skill):
            return NotImplemented
        return (self.name, self.category, self.proficiency) == (other.name, other.category, other.proficiency)


class SkillManager:
    """Manages a collection of skills."""

    def __init__(self):
        self._skills = []

    def add(self, skill: Skill) -> None:
        """Add a skill to the manager."""
        if not isinstance(skill, Skill):
            raise TypeError("Only Skill objects can be added")
        self._skills.append(skill)

    def remove(self, skill_name: str) -> bool:
        """Remove a skill by name. Returns True if removed, False if not found."""
        for i, skill in enumerate(self._skills):
            if skill.name == skill_name:
                self._skills.pop(i)
                return True
        return False

    def update(self, skill_name: str, new_proficiency: int) -> bool:
        """Update the proficiency of a skill by name. Returns True if updated, False if not found."""
        if not isinstance(new_proficiency, int) or not (0 <= new_proficiency <= 100):
            raise ValueError("Proficiency must be an integer between 0 and 100")
        for skill in self._skills:
            if skill.name == skill_name:
                skill.proficiency = new_proficiency
                return True
        return False

    def list_all(self) -> list:
        """Return a list of all skills."""
        return list(self._skills)

    def list_by_category(self, category: str) -> list:
        """Return a list of skills in a given category."""
        return [skill for skill in self._skills if skill.category == category]

    def get(self, skill_name: str):
        """Retrieve a skill by name, or None if not found."""
        for skill in self._skills:
            if skill.name == skill_name:
                return skill
        return None