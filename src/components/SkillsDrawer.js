import React, { useState } from 'react';
import './SkillsDrawer.css';

const SkillsDrawer = () => {
  const [skills, setSkills] = useState([]);
  const [newSkill, setNewSkill] = useState('');
  const [editingIndex, setEditingIndex] = useState(null);
  const [editingSkill, setEditingSkill] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const handleAddSkill = () => {
    if (newSkill.trim() === '') return;
    setSkills([...skills, newSkill.trim()]);
    setNewSkill('');
  };

  const handleDeleteSkill = (index) => {
    setSkills(skills.filter((_, i) => i !== index));
  };

  const handleEditSkill = (index) => {
    setEditingIndex(index);
    setEditingSkill(skills[index]);
  };

  const handleSaveEdit = () => {
    const updatedSkills = skills.map((skill, i) =>
      i === editingIndex ? editingSkill.trim() : skill
    );
    setSkills(updatedSkills);
    setEditingIndex(null);
    setEditingSkill('');
  };

  const toggleDrawer = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className="skills-drawer-container">
      <button className="toggle-button" onClick={toggleDrawer}>
        {isOpen ? 'Close Skills Panel' : 'Open Skills Panel'}
      </button>
      {isOpen && (
        <div className="skills-drawer">
          <h2>Skills</h2>
          <div className="add-skill">
            <input
              type="text"
              placeholder="Add a skill..."
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleAddSkill(); }}
              data-testid="new-skill-input"
            />
            <button onClick={handleAddSkill} data-testid="add-skill-button">Add</button>
          </div>
          <ul className="skills-list" data-testid="skills-list">
            {skills.length === 0 && <li>No skills added yet.</li>}
            {skills.map((skill, index) => (
              <li key={index} className="skill-item" data-testid={`skill-${index}`}>
                {editingIndex === index ? (
                  <>
                    <input
                      type="text"
                      value={editingSkill}
                      onChange={(e) => setEditingSkill(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') handleSaveEdit(); }}
                      data-testid="edit-skill-input"
                    />
                    <button onClick={handleSaveEdit} data-testid="save-edit-button">Save</button>
                  </>
                ) : (
                  <>
                    <span>{skill}</span>
                    <button onClick={() => handleEditSkill(index)} data-testid="edit-button">Edit</button>
                    <button onClick={() => handleDeleteSkill(index)} data-testid="delete-button">Delete</button>
                  </>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default SkillsDrawer;