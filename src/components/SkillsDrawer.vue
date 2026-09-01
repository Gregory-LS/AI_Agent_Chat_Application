<template>
  <div v-if="isOpen" class="drawer-overlay" @click.self="close">
    <div class="drawer-panel" role="dialog" aria-label="Skills drawer">
      <div class="drawer-header">
        <h2>Select Starter Skills</h2>
        <button class="close-btn" @click="close" aria-label="Close drawer">&times;</button>
      </div>
      <div class="drawer-body">
        <div
          v-for="skill in starterSkills"
          :key="skill.name"
          class="skill-card"
          :class="{ selected: isSelected(skill) }"
          @click="toggleSkill(skill)"
          tabindex="0"
          @keydown.enter="toggleSkill(skill)"
          @keydown.space.prevent="toggleSkill(skill)"
          role="checkbox"
          :aria-checked="isSelected(skill).toString()"
        >
          <span class="skill-icon">{{ skill.icon }}</span>
          <span class="skill-name">{{ skill.name }}</span>
        </div>
      </div>
      <div class="drawer-footer">
        <button @click="close" class="btn btn-secondary">Cancel</button>
        <button @click="confirmAndClose" class="btn btn-primary">Add Skills</button>
      </div>
    </div>
  </div>
</template>

<script>
import { useSkillsStore } from '@/stores/skills';

export default {
  name: 'SkillsDrawer',
  props: {
    isOpen: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['close', 'update:selection'],
  setup(props, { emit }) {
    const store = useSkillsStore();
    const starterSkills = [
      { name: 'Python', icon: '🐍' },
      { name: 'JavaScript', icon: '📜' },
      { name: 'SQL', icon: '🗄️' },
      { name: 'Git', icon: '🔀' },
      { name: 'Docker', icon: '🐳' },
      { name: 'Kubernetes', icon: '☸️' },
    ];

    const toggleSkill = (skill) => {
      store.toggleSkill(skill);
    };

    const isSelected = (skill) => {
      return store.selectedSkills.some(s => s.name === skill.name);
    };

    const close = () => {
      emit('close');
    };

    const confirmAndClose = () => {
      emit('update:selection', store.selectedSkills);
      store.confirmSelection();
      close();
    };

    return {
      starterSkills,
      toggleSkill,
      isSelected,
      close,
      confirmAndClose,
    };
  },
};
</script>

<style scoped>
@import './SkillsDrawer.css';
</style>
