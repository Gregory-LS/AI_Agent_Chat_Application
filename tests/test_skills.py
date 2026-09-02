import pytest
from skills import Skill, SkillManager


class TestSkill:
    def test_skill_creation(self):
        skill = Skill("Python", "Programming", 80)
        assert skill.name == "Python"
        assert skill.category == "Programming"
        assert skill.proficiency == 80

    def test_skill_proficiency_out_of_range_low(self):
        with pytest.raises(ValueError):
            Skill("Python", "Programming", -1)

    def test_skill_proficiency_out_of_range_high(self):
        with pytest.raises(ValueError):
            Skill("Python", "Programming", 101)

    def test_skill_proficiency_non_integer(self):
        with pytest.raises(ValueError):
            Skill("Python", "Programming", "high")

    def test_skill_equality(self):
        s1 = Skill("Python", "Programming", 80)
        s2 = Skill("Python", "Programming", 80)
        assert s1 == s2

    def test_skill_inequality(self):
        s1 = Skill("Python", "Programming", 80)
        s2 = Skill("Python", "Programming", 90)
        assert s1 != s2

    def test_skill_repr(self):
        skill = Skill("Python", "Programming", 80)
        assert repr(skill) == "Skill(name='Python', category='Programming', proficiency=80)"


class TestSkillManager:
    def test_add_skill(self):
        mgr = SkillManager()
        skill = Skill("Python", "Programming", 80)
        mgr.add(skill)
        assert mgr.list_all() == [skill]

    def test_add_non_skill_raises_typeerror(self):
        mgr = SkillManager()
        with pytest.raises(TypeError):
            mgr.add("not a skill")

    def test_remove_existing_skill(self):
        mgr = SkillManager()
        skill = Skill("Python", "Programming", 80)
        mgr.add(skill)
        assert mgr.remove("Python") is True
        assert mgr.list_all() == []

    def test_remove_nonexistent_skill(self):
        mgr = SkillManager()
        assert mgr.remove("Nonexistent") is False

    def test_update_existing_skill(self):
        mgr = SkillManager()
        skill = Skill("Python", "Programming", 80)
        mgr.add(skill)
        assert mgr.update("Python", 90) is True
        assert skill.proficiency == 90

    def test_update_nonexistent_skill(self):
        mgr = SkillManager()
        assert mgr.update("Nonexistent", 50) is False

    def test_update_invalid_proficiency(self):
        mgr = SkillManager()
        skill = Skill("Python", "Programming", 80)
        mgr.add(skill)
        with pytest.raises(ValueError):
            mgr.update("Python", 150)

    def test_list_all_empty(self):
        mgr = SkillManager()
        assert mgr.list_all() == []

    def test_list_by_category(self):
        mgr = SkillManager()
        s1 = Skill("Python", "Programming", 80)
        s2 = Skill("SQL", "Programming", 70)
        s3 = Skill("Excel", "Productivity", 90)
        mgr.add(s1)
        mgr.add(s2)
        mgr.add(s3)
        programming_skills = mgr.list_by_category("Programming")
        assert programming_skills == [s1, s2]

    def test_get_existing_skill(self):
        mgr = SkillManager()
        skill = Skill("Python", "Programming", 80)
        mgr.add(skill)
        assert mgr.get("Python") == skill

    def test_get_nonexistent_skill(self):
        mgr = SkillManager()
        assert mgr.get("Nonexistent") is None
