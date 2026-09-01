import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SkillsDrawer from './SkillsDrawer';

// Mock the skillsService
jest.mock('../../services/skillsService', () => ({
  skillsService: {
    getSkills: jest.fn(),
    createSkill: jest.fn(),
    updateSkill: jest.fn(),
    deleteSkill: jest.fn(),
  },
}));

import { skillsService } from '../../services/skillsService' as any;

const mockSkills = [
  { id: '1', name: 'React', description: 'UI library', level: 'advanced' },
  { id: '2', name: 'Node', description: 'Runtime', level: 'intermediate' },
];

describe('SkillsDrawer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('opens drawer and fetches skills on button click', async () => {
    (skillsService.getSkills as jest.Mock).mockResolvedValue(mockSkills);
    render(<SkillsDrawer />);
    
    const openButton = screen.getByText('Manage Skills');
    fireEvent.click(openButton);
    
    await waitFor(() => {
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('Node')).toBeInTheDocument();
    });
  });

  test('displays error message when fetch fails', async () => {
    (skillsService.getSkills as jest.Mock).mockRejectedValue(new Error('Network error'));
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText('Manage Skills'));
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load skills')).toBeInTheDocument();
    });
  });

  test('creates a new skill', async () => {
    (skillsService.getSkills as jest.Mock).mockResolvedValue([]);
    const newSkill = { id: '3', name: 'TypeScript', description: 'Typed JS', level: 'beginner' };
    (skillsService.createSkill as jest.Mock).mockResolvedValue(newSkill);
    
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText('Manage Skills'));
    
    await waitFor(() => screen.getByText('Skills'));
    
    fireEvent.change(screen.getByLabelText('Name:'), { target: { value: 'TypeScript' } });
    fireEvent.change(screen.getByLabelText('Description:'), { target: { value: 'Typed JS' } });
    fireEvent.change(screen.getByLabelText('Level:'), { target: { value: 'beginner' } });
    fireEvent.click(screen.getByText('Add'));
    
    await waitFor(() => {
      expect(screen.getByText('TypeScript')).toBeInTheDocument();
    });
  });

  test('edits a skill', async () => {
    (skillsService.getSkills as jest.Mock).mockResolvedValue(mockSkills);
    const updatedSkill = { id: '1', name: 'React', description: 'Updated description', level: 'advanced' };
    (skillsService.updateSkill as jest.Mock).mockResolvedValue(updatedSkill);
    
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText('Manage Skills'));
    
    await waitFor(() => screen.getByText('React'));
    
    const editButtons = screen.getAllByText('Edit');
    fireEvent.click(editButtons[0]);
    
    const descriptionInput = screen.getByLabelText('Description:');
    fireEvent.change(descriptionInput, { target: { value: 'Updated description' } });
    fireEvent.click(screen.getByText('Update'));
    
    await waitFor(() => {
      expect(screen.getByText('Updated description')).toBeInTheDocument();
    });
  });

  test('deletes a skill', async () => {
    (skillsService.getSkills as jest.Mock).mockResolvedValue(mockSkills);
    (skillsService.deleteSkill as jest.Mock).mockResolvedValue(undefined);
    
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText('Manage Skills'));
    
    await waitFor(() => screen.getByText('React'));
    
    const deleteButtons = screen.getAllByText('Delete');
    fireEvent.click(deleteButtons[0]);
    
    await waitFor(() => {
      expect(screen.queryByText('React')).not.toBeInTheDocument();
    });
  });

  test('cancels edit mode', async () => {
    (skillsService.getSkills as jest.Mock).mockResolvedValue(mockSkills);
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText('Manage Skills'));
    
    await waitFor(() => screen.getByText('React'));
    
    fireEvent.click(screen.getAllByText('Edit')[0]);
    fireEvent.click(screen.getByText('Cancel'));
    
    expect(screen.getByText('Add Skill')).toBeInTheDocument();
    expect(screen.getByLabelText('Name:')).toHaveValue('');
  });
});