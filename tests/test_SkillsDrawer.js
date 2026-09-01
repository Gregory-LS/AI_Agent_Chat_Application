import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SkillsDrawer from '../src/components/SkillsDrawer';

describe('SkillsDrawer', () => {
  test('renders toggle button', () => {
    render(<SkillsDrawer />);
    expect(screen.getByText(/Open Skills Panel/i)).toBeInTheDocument();
  });

  test('opens drawer on toggle', () => {
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText(/Open Skills Panel/i));
    expect(screen.getByText('Skills')).toBeInTheDocument();
  });

  test('adds a skill', () => {
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText(/Open Skills Panel/i));
    const input = screen.getByTestId('new-skill-input');
    fireEvent.change(input, { target: { value: 'React' } });
    fireEvent.click(screen.getByTestId('add-skill-button'));
    expect(screen.getByText('React')).toBeInTheDocument();
  });

  test('deletes a skill', () => {
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText(/Open Skills Panel/i));
    const input = screen.getByTestId('new-skill-input');
    fireEvent.change(input, { target: { value: 'React' } });
    fireEvent.click(screen.getByTestId('add-skill-button'));
    const deleteButton = screen.getByTestId('delete-button');
    fireEvent.click(deleteButton);
    expect(screen.queryByText('React')).not.toBeInTheDocument();
  });

  test('edits a skill', () => {
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText(/Open Skills Panel/i));
    const input = screen.getByTestId('new-skill-input');
    fireEvent.change(input, { target: { value: 'React' } });
    fireEvent.click(screen.getByTestId('add-skill-button'));
    const editButton = screen.getByTestId('edit-button');
    fireEvent.click(editButton);
    const editInput = screen.getByTestId('edit-skill-input');
    fireEvent.change(editInput, { target: { value: 'Vue' } });
    fireEvent.click(screen.getByTestId('save-edit-button'));
    expect(screen.getByText('Vue')).toBeInTheDocument();
    expect(screen.queryByText('React')).not.toBeInTheDocument();
  });

  test('shows empty state when no skills', () => {
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText(/Open Skills Panel/i));
    expect(screen.getByText('No skills added yet.')).toBeInTheDocument();
  });

  test('does not add empty skill', () => {
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText(/Open Skills Panel/i));
    const input = screen.getByTestId('new-skill-input');
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.click(screen.getByTestId('add-skill-button'));
    expect(screen.getByText('No skills added yet.')).toBeInTheDocument();
  });

  test('adds skill on Enter key', () => {
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText(/Open Skills Panel/i));
    const input = screen.getByTestId('new-skill-input');
    fireEvent.change(input, { target: { value: 'Node.js' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    expect(screen.getByText('Node.js')).toBeInTheDocument();
  });

  test('saves edit on Enter key', () => {
    render(<SkillsDrawer />);
    fireEvent.click(screen.getByText(/Open Skills Panel/i));
    const input = screen.getByTestId('new-skill-input');
    fireEvent.change(input, { target: { value: 'React' } });
    fireEvent.click(screen.getByTestId('add-skill-button'));
    const editButton = screen.getByTestId('edit-button');
    fireEvent.click(editButton);
    const editInput = screen.getByTestId('edit-skill-input');
    fireEvent.change(editInput, { target: { value: 'Angular' } });
    fireEvent.keyDown(editInput, { key: 'Enter', code: 'Enter' });
    expect(screen.getByText('Angular')).toBeInTheDocument();
  });
});