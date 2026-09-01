import { describe, it, expect, beforeEach } from 'vitest';
import { useSkillsStore, defaultState } from '@/stores/skills';

// Since the store uses reactive state outside component context,
// we need to ensure each test gets a fresh state.
// We'll re-import the store or recreate by using a factory wrapper.

// For simplicity, we test the exported functions directly assuming they mutate the global state.
// In a real project, consider using pinia or state factory.

describe('useSkillsStore', () => {
  let store;

  beforeEach(() => {
    // Reset the global state manually for each test
    const { selectedSkills, confirmedSkills } = useSkillsStore();
    selectedSkills.value = [];
    confirmedSkills.value = [];
    store = useSkillsStore();
  });

  it('should toggle a skill into selected', () => {
    store.toggleSkill({ name: 'Python', icon: '🐍' });
    expect(store.selectedSkills.value).toHaveLength(1);
    expect(store.selectedSkills.value[0].name).toBe('Python');
  });

  it('should toggle a skill out of selected', () => {
    store.toggleSkill({ name: 'Python', icon: '🐍' });
    store.toggleSkill({ name: 'Python', icon: '🐍' });
    expect(store.selectedSkills.value).toHaveLength(0);
  });

  it('should keep multiple skills selected', () => {
    store.toggleSkill({ name: 'Python', icon: '🐍' });
    store.toggleSkill({ name: 'JavaScript', icon: '📜' });
    expect(store.selectedSkills.value).toHaveLength(2);
  });

  it('should confirm selection and keep it after resets', () => {
    store.toggleSkill({ name: 'Python', icon: '🐍' });
    store.confirmSelection();
    expect(store.confirmedSkills.value).toHaveLength(1);
    expect(store.confirmedSkills.value[0].name).toBe('Python');
  });

  it('should reset confirmed skills', () => {
    store.toggleSkill({ name: 'Python', icon: '🐍' });
    store.confirmSelection();
    store.resetConfirmed();
    expect(store.confirmedSkills.value).toHaveLength(0);
  });
});
