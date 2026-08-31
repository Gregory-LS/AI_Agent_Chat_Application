import React, { useState } from 'react';

export interface Skill {
  id: string;
  name: string;
  description: string;
  systemPrompt: string;
  model?: string;
  enabled: boolean;
}

interface SkillPanelProps {
  initialSkills?: Skill[];
  availableModels?: string[];
  initialDefaultModel?: string;
}

const PREVIEW_LENGTH = 120;

const SkillPanel: React.FC<SkillPanelProps> = ({
  initialSkills = [],
  availableModels = [],
  initialDefaultModel = '',
}) => {
  const [skills, setSkills] = useState<Skill[]>(initialSkills);
  const [defaultModel, setDefaultModel] = useState<string>(initialDefaultModel);
  const [expandedPrompt, setExpandedPrompt] = useState<string | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);

  const enabledCount = skills.filter((skill) => skill.enabled).length;

  const moveSkill = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= skills.length) return;
    const reordered = [...skills];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    setSkills(reordered);
  };

  const handleDrop = (targetIndex: number) => {
    if (dragIndex === null) return;
    if (dragIndex === targetIndex) {
      setDragIndex(null);
      return;
    }
    const reordered = [...skills];
    const [moved] = reordered.splice(dragIndex, 1);
    reordered.splice(targetIndex, 0, moved);
    setSkills(reordered);
    setDragIndex(null);
  };

  const toggleSkill = (id: string, enabled: boolean) => {
    setSkills((prev) => prev.map((skill) => (skill.id === id ? { ...skill, enabled } : skill)));
  };

  const updateSkillModel = (id: string, model: string) => {
    setSkills((prev) =>
      prev.map((skill) =>
        skill.id === id
          ? { ...skill, model: model === defaultModel ? undefined : model }
          : skill,
      ),
    );
  };

  const togglePromptPreview = (id: string) => {
    setExpandedPrompt((prev) => (prev === id ? null : id));
  };

  const previewPrompt = (prompt: string) =>
    prompt.length > PREVIEW_LENGTH ? `${prompt.slice(0, PREVIEW_LENGTH)}…` : prompt;

  return (
    <div className='skill-panel' style={styles.panel}>
      <div style={styles.header}>
        <h2 style={styles.title}>Skills</h2>
        <span style={styles.countBadge}>
          {enabledCount} / {skills.length} enabled
        </span>
      </div>

      <div style={styles.defaultModelRow}>
        <label htmlFor='default-model' style={styles.label}>
          Default model:
        </label>
        <select
          id='default-model'
          value={defaultModel}
          onChange={(e) => setDefaultModel(e.target.value)}
          style={styles.select}
        >
          <option value=''>None</option>
          {availableModels.map((model) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
      </div>

      {skills.length === 0 ? (
        <p style={styles.empty}>No skills configured.</p>
      ) : (
        <ul style={styles.list}>
          {skills.map((skill, index) => {
            const effectiveModel = skill.model ?? defaultModel;
            const promptPreview = previewPrompt(skill.systemPrompt);
            const isExpanded = expandedPrompt === skill.id;

            return (
              <li
                key={skill.id}
                style={{ ...styles.item, opacity: dragIndex === index ? 0.5 : 1 }}
                draggable
                onDragStart={() => setDragIndex(index)}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  handleDrop(index);
                }}
                onDragEnd={() => setDragIndex(null)}
              >
                <div style={styles.itemHeader}>
                  <input
                    type='checkbox'
                    checked={skill.enabled}
                    onChange={(e) => toggleSkill(skill.id, e.target.checked)}
                    aria-label={`Toggle ${skill.name}`}
                  />
                  <strong style={styles.skillName}>{skill.name}</strong>
                  <span style={styles.reorderButtons}>
                    <button
                      onClick={() => moveSkill(index, -1)}
                      disabled={index === 0}
                      aria-label={`Move ${skill.name} up`}
                      style={styles.button}
                    >
                      ↑
                    </button>
                    <button
                      onClick={() => moveSkill(index, 1)}
                      disabled={index === skills.length - 1}
                      aria-label={`Move ${skill.name} down`}
                      style={styles.button}
                    >
                      ↓
                    </button>
                  </span>
                </div>

                {skill.description && <p style={styles.description}>{skill.description}</p>}

                <div style={styles.modelRow}>
                  <label style={styles.label}>Model:</label>
                  <select
                    value={effectiveModel}
                    onChange={(e) => updateSkillModel(skill.id, e.target.value)}
                    style={styles.select}
                  >
                    <option value={defaultModel}>
                      {defaultModel ? `Use default (${defaultModel})` : 'No default'}
                    </option>
                    {availableModels
                      .filter((model) => model !== defaultModel)
                      .map((model) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))}
                  </select>
                </div>

                <div style={styles.promptBlock}>
                  <button
                    type='button'
                    onClick={() => togglePromptPreview(skill.id)}
                    style={styles.promptToggle}
                  >
                    {isExpanded ? 'Hide' : 'Preview'} system prompt
                  </button>
                  <pre style={styles.promptPreview}>
                    {isExpanded ? skill.systemPrompt : promptPreview}
                  </pre>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  panel: {
    fontFamily: 'system-ui, sans-serif',
    maxWidth: '720px',
    margin: '0 auto',
    padding: '1rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    background: '#fff',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '1rem',
  },
  title: {
    margin: 0,
    fontSize: '1.25rem',
  },
  countBadge: {
    background: '#eef2ff',
    color: '#4338ca',
    borderRadius: '999px',
    padding: '0.25rem 0.75rem',
    fontSize: '0.875rem',
  },
  defaultModelRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '1rem',
  },
  label: {
    fontWeight: 600,
  },
  select: {
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    border: '1px solid #ccc',
  },
  list: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  item: {
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    padding: '0.75rem',
    background: '#f9fafb',
    cursor: 'grab',
  },
  itemHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  skillName: {
    flex: 1,
  },
  reorderButtons: {
    display: 'flex',
    gap: '0.25rem',
  },
  button: {
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    border: '1px solid #ccc',
    background: '#fff',
    cursor: 'pointer',
  },
  description: {
    margin: '0.5rem 0',
    color: '#6b7280',
    fontSize: '0.875rem',
  },
  modelRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginTop: '0.5rem',
  },
  promptBlock: {
    marginTop: '0.5rem',
  },
  promptToggle: {
    background: 'none',
    border: 'none',
    color: '#2563eb',
    cursor: 'pointer',
    padding: 0,
    fontSize: '0.875rem',
  },
  promptPreview: {
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    background: '#f3f4f6',
    borderRadius: '4px',
    padding: '0.5rem',
    fontSize: '0.8125rem',
    maxHeight: '150px',
    overflowY: 'auto',
  },
  empty: {
    color: '#6b7280',
    fontStyle: 'italic',
  },
};

export default SkillPanel;
