import { reactive, toRefs } from 'vue';

const state = reactive({
  selectedSkills: [],
  confirmedSkills: [],
});

export function useSkillsStore() {
  const toggleSkill = (skill) => {
    const index = state.selectedSkills.findIndex(s => s.name === skill.name);
    if (index >= 0) {
      state.selectedSkills.splice(index, 1);
    } else {
      state.selectedSkills.push({ ...skill });
    }
  };

  const confirmSelection = () => {
    state.confirmedSkills = state.selectedSkills.map(s => ({ ...s }));
  };

  const resetConfirmed = () => {
    state.confirmedSkills = [];
  };

  return {
    ...toRefs(state),
    toggleSkill,
    confirmSelection,
    resetConfirmed,
  };
}
