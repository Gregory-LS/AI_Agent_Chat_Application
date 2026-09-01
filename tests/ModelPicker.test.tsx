import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ModelPicker from '../src/components/ModelPicker';

describe('ModelPicker', () => {
  const models = ['GPT-3', 'GPT-4', 'BERT', 'T5'];
  const onSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders all model options', () => {
    render(<ModelPicker models={models} onSelect={onSelect} />);
    const select = screen.getByTestId('model-picker');
    expect(select).toBeInTheDocument();
    const options = screen.getAllByRole('option');
    // One placeholder + 4 models
    expect(options).toHaveLength(5);
    expect(options[0]).toHaveTextContent('Select a model');
    expect(options[1]).toHaveTextContent('GPT-3');
    expect(options[2]).toHaveTextContent('GPT-4');
    expect(options[3]).toHaveTextContent('BERT');
    expect(options[4]).toHaveTextContent('T5');
  });

  it('displays the selected model', () => {
    render(<ModelPicker models={models} selectedModel="GPT-4" onSelect={onSelect} />);
    const select = screen.getByTestId('model-picker') as HTMLSelectElement;
    expect(select.value).toBe('GPT-4');
  });

  it('calls onSelect when a model is selected', () => {
    render(<ModelPicker models={models} onSelect={onSelect} />);
    const select = screen.getByTestId('model-picker');
    fireEvent.change(select, { target: { value: 'BERT' } });
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith('BERT');
  });

  it('does not call onSelect when placeholder is selected', () => {
    render(<ModelPicker models={models} onSelect={onSelect} />);
    const select = screen.getByTestId('model-picker');
    // Fire change with empty value (placeholder) shouldn't trigger
    fireEvent.change(select, { target: { value: '' } });
    expect(onSelect).not.toHaveBeenCalled();
  });

  it('disables the select when disabled prop is true', () => {
    render(<ModelPicker models={models} onSelect={onSelect} disabled />);
    const select = screen.getByTestId('model-picker');
    expect(select).toBeDisabled();
  });

  it('disables placeholder option correctly', () => {
    render(<ModelPicker models={models} onSelect={onSelect} />);
    const placeholderOption = screen.getByText('Select a model') as HTMLOptionElement;
    expect(placeholderOption.disabled).toBe(true);
  });

  it('renders with custom placeholder', () => {
    render(<ModelPicker models={models} onSelect={onSelect} placeholder="Choose model" />);
    expect(screen.getByText('Choose model')).toBeInTheDocument();
  });

  it('handles empty models array', () => {
    render(<ModelPicker models={[]} onSelect={onSelect} />);
    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(1); // only placeholder
  });
});
