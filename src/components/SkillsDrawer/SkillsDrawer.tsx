import React, { useState, useEffect, useCallback } from 'react';

interface Skill {
  id: string;
  name: string;
  description: string;
  level: 'beginner' | 'intermediate' | 'advanced';
}

type SkillFormData = Omit<Skill, 'id'>;

// Mock API service (replace with real API calls)
const skillsService = {
  async getSkills(): Promise<Skill[]> {
    // Simulate fetching from API
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve([
          { id: '1', name: 'React', description: 'Frontend library', level: 'advanced' },
          { id: '2', name: 'Node.js', description: 'Backend runtime', level: 'intermediate' },
        ]);
      }, 300);
    });
  },

  async createSkill(skill: SkillFormData): Promise<Skill> {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ id: Date.now().toString(), ...skill });
      }, 200);
    });
  },

  async updateSkill(id: string, skill: SkillFormData): Promise<Skill> {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ id, ...skill });
      }, 200);
    });
  },

  async deleteSkill(id: string): Promise<void> {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve();
      }, 200);
    });
  },
};

const SkillsDrawer: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null);
  const [formData, setFormData] = useState<SkillFormData>({
    name: '',
    description: '',
    level: 'beginner',
  });

  const fetchSkills = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await skillsService.getSkills();
      setSkills(data);
    } catch (err) {
      setError('Failed to load skills');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchSkills();
    }
  }, [isOpen, fetchSkills]);

  const handleOpen = () => setIsOpen(true);
  const handleClose = () => {
    setIsOpen(false);
    setEditingSkill(null);
    setFormData({ name: '', description: '', level: 'beginner' });
    setError(null);
  };

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (editingSkill) {
        const updated = await skillsService.updateSkill(editingSkill.id, formData);
        setSkills((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
        setEditingSkill(null);
      } else {
        const created = await skillsService.createSkill(formData);
        setSkills((prev) => [...prev, created]);
      }
      setFormData({ name: '', description: '', level: 'beginner' });
    } catch (err) {
      setError('Failed to save skill');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (skill: Skill) => {
    setEditingSkill(skill);
    setFormData({ name: skill.name, description: skill.description, level: skill.level });
  };

  const handleDelete = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      await skillsService.deleteSkill(id);
      setSkills((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      setError('Failed to delete skill');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingSkill(null);
    setFormData({ name: '', description: '', level: 'beginner' });
  };

  return (
    <>
      <button onClick={handleOpen} aria-label="Open skills drawer">
        Manage Skills
      </button>
      {isOpen && (
        <div className="drawer-overlay" onClick={handleClose}>
          <div className="drawer" onClick={(e) => e.stopPropagation()}>
            <h2>Skills</h2>
            <button onClick={handleClose} aria-label="Close drawer">Close</button>
            {error && <div className="error">{error}</div>}
            {loading && <div className="loading">Loading...</div>}
            <ul>
              {skills.map((skill) => (
                <li key={skill.id}>
                  <strong>{skill.name}</strong> - {skill.level}
                  <p>{skill.description}</p>
                  <button onClick={() => handleEdit(skill)}>Edit</button>
                  <button onClick={() => handleDelete(skill.id)}>Delete</button>
                </li>
              ))}
            </ul>
            <h3>{editingSkill ? 'Edit Skill' : 'Add Skill'}</h3>
            <form onSubmit={handleSubmit}>
              <label>
                Name:
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleFormChange}
                  required
                />
              </label>
              <label>
                Description:
                <input
                  type="text"
                  name="description"
                  value={formData.description}
                  onChange={handleFormChange}
                />
              </label>
              <label>
                Level:
                <select name="level" value={formData.level} onChange={handleFormChange}>
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </label>
              <button type="submit" disabled={loading}>
                {editingSkill ? 'Update' : 'Add'}
              </button>
              {editingSkill && <button type="button" onClick={handleCancelEdit}>Cancel</button>}
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default SkillsDrawer;