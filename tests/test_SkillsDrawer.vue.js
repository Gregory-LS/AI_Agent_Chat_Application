import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import SkillsDrawer from '@/components/SkillsDrawer.vue';

// Mock the skills store
const mockStore = {
  selectedSkills: [],
  toggleSkill: vi.fn(),
  confirmSelection: vi.fn(),
};

vi.mock('@/stores/skills', () => ({
  useSkillsStore: () => mockStore,
}));

describe('SkillsDrawer', () => {
  const starterSkills = [
    { name: 'Python', icon: '🐍' },
    { name: 'JavaScript', icon: '📜' },
    { name: 'SQL', icon: '🗄️' },
    { name: 'Git', icon: '🔀' },
    { name: 'Docker', icon: '🐳' },
    { name: 'Kubernetes', icon: '☸️' },
  ];

  it('renders when isOpen is true', () => {
    const wrapper = mount(SkillsDrawer, {
      props: { isOpen: true },
    });
    expect(wrapper.find('.drawer-panel').exists()).toBe(true);
    expect(wrapper.text()).toContain('Select Starter Skills');
  });

  it('does not render when isOpen is false', () => {
    const wrapper = mount(SkillsDrawer, {
      props: { isOpen: false },
    });
    expect(wrapper.find('.drawer-panel').exists()).toBe(false);
  });

  it('displays all starter skills', () => {
    const wrapper = mount(SkillsDrawer, {
      props: { isOpen: true },
    });
    const cards = wrapper.findAll('.skill-card');
    expect(cards).toHaveLength(6);
    expect(cards[0].text()).toContain('Python');
    expect(cards[1].text()).toContain('JavaScript');
  });

  it('calls store.toggleSkill when skill card is clicked', async () => {
    const wrapper = mount(SkillsDrawer, {
      props: { isOpen: true },
    });
    const firstCard = wrapper.findAll('.skill-card')[0];
    await firstCard.trigger('click');
    expect(mockStore.toggleSkill).toHaveBeenCalledWith(starterSkills[0]);
  });

  it('emits close event when close button is clicked', async () => {
    const wrapper = mount(SkillsDrawer, {
      props: { isOpen: true },
    });
    await wrapper.find('.close-btn').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('emits update:selection and closes when Add Skills is clicked', async () => {
    const wrapper = mount(SkillsDrawer, {
      props: { isOpen: true },
    });
    await wrapper.find('.btn-primary').trigger('click');
    expect(wrapper.emitted('update:selection')).toBeTruthy();
    expect(mockStore.confirmSelection).toHaveBeenCalled();
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('emits close when Cancel is clicked', async () => {
    const wrapper = mount(SkillsDrawer, {
      props: { isOpen: true },
    });
    await wrapper.find('.btn-secondary').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });
});
