export interface Skill {
  id: string;
  name: string;
  description: string;
  level: 'beginner' | 'intermediate' | 'advanced';
}

export type SkillFormData = Omit<Skill, 'id'>;

// Mock API service – replace with real HTTP calls
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

let nextId = 3;
const fakeSkills: Skill[] = [
  { id: '1', name: 'React', description: 'Frontend library', level: 'advanced' },
  { id: '2', name: 'Node.js', description: 'Backend runtime', level: 'intermediate' },
];

export const skillsService = {
  async getSkills(): Promise<Skill[]> {
    await delay(300);
    return [...fakeSkills];
  },

  async createSkill(skill: SkillFormData): Promise<Skill> {
    await delay(200);
    const newSkill: Skill = { id: String(nextId++), ...skill };
    fakeSkills.push(newSkill);
    return newSkill;
  },

  async updateSkill(id: string, skill: SkillFormData): Promise<Skill> {
    await delay(200);
    const index = fakeSkills.findIndex((s) => s.id === id);
    if (index === -1) throw new Error('Skill not found');
    fakeSkills[index] = { id, ...skill };
    return fakeSkills[index];
  },

  async deleteSkill(id: string): Promise<void> {
    await delay(200);
    const index = fakeSkills.findIndex((s) => s.id === id);
    if (index === -1) throw new Error('Skill not found');
    fakeSkills.splice(index, 1);
  },
};