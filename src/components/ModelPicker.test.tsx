import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ModelPicker } from './ModelPicker';
import type { Model } from '../types';

const models: Model[] = [
  { id: 'model-a', name: 'Model A', description: 'First model' },
  { id: 'model-b', name: 'Model B', description: 'Second model' },
  { id: 'model-c', name: 'Model C' },
];

describe('ModelPicker', () => {
  it('shows the selected model name when a matching value is provided', () => {
    render(<ModelPicker value='model-b' onChange={jest.fn()} models={models} />);
    expect(screen.getByText('Model B')).toBeInTheDocument();
  });

  it('shows the placeholder when no value is selected', () => {
    render(<ModelPicker onChange={jest.fn()} models={models} />);
    expect(screen.getByText('Select a model…')).toBeInTheDocument();
  });

  it('opens the listbox when the trigger is clicked', () => {
    render(<ModelPicker onChange={jest.fn()} models={models} />);
    fireEvent.click(screen.getByRole('button', { name: /model picker/i }));
    expect(screen.getByRole('listbox')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /Model A/ })).toBeInTheDocument();
  });

  it('calls onChange and closes the dropdown when an option is selected', () => {
    const handleChange = jest.fn();
    render(<ModelPicker onChange={handleChange} models={models} />);
    fireEvent.click(screen.getByRole('button', { name: /model picker/i }));
    fireEvent.click(screen.getByText('Model B'));
    expect(handleChange).toHaveBeenCalledWith('model-b');
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('filters models by the search query', () => {
    render(<ModelPicker onChange={jest.fn()} models={models} />);
    fireEvent.click(screen.getByRole('button', { name: /model picker/i }));
    const search = screen.getByRole('combobox', { name: /search models/i });
    fireEvent.change(search, { target: { value: 'Model C' } });
    expect(screen.getByRole('option', { name: /Model C/ })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: /Model A/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('option', { name: /Model B/ })).not.toBeInTheDocument();
  });

  it('shows a message when no models match', () => {
    render(<ModelPicker onChange={jest.fn()} models={models} />);
    fireEvent.click(screen.getByRole('button', { name: /model picker/i }));
    fireEvent.change(screen.getByRole('combobox', { name: /search models/i }), {
      target: { value: 'zzz' },
    });
    expect(screen.getByText('No models found.')).toBeInTheDocument();
  });

  it('does not open when disabled', () => {
    render(<ModelPicker onChange={jest.fn()} models={models} disabled />);
    fireEvent.click(screen.getByRole('button', { name: /model picker/i }));
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('shows loading state while fetching models', async () => {
    let resolveFetch!: (value: Model[]) => void;
    const deferred = new Promise<Model[]>((resolve) => {
      resolveFetch = resolve;
    });
    const fetchModelsImpl = jest.fn(() => deferred);

    render(<ModelPicker onChange={jest.fn()} fetchModels={fetchModelsImpl} />);
    fireEvent.click(screen.getByRole('button', { name: /model picker/i }));

    expect(screen.getByText('Loading models…')).toBeInTheDocument();

    resolveFetch(models);
    expect(await screen.findByRole('option', { name: /Model A/ })).toBeInTheDocument();
  });

  it('shows an error when fetching models fails and retries', async () => {
    const fetchModelsImpl = jest
      .fn()
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce(models);

    render(<ModelPicker onChange={jest.fn()} fetchModels={fetchModelsImpl} />);
    fireEvent.click(screen.getByRole('button', { name: /model picker/i }));

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Network error'));
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() => expect(screen.getByText('Model A')).toBeInTheDocument());
    expect(fetchModelsImpl).toHaveBeenCalledTimes(2);
  });

  it('selects a model with the keyboard', () => {
    const handleChange = jest.fn();
    render(<ModelPicker onChange={handleChange} models={models} />);
    fireEvent.click(screen.getByRole('button', { name: /model picker/i }));

    const search = screen.getByRole('combobox', { name: /search models/i });
    fireEvent.keyDown(search, { key: 'ArrowDown' });
    fireEvent.keyDown(search, { key: 'Enter' });

    expect(handleChange).toHaveBeenCalledWith('model-b');
  });
});
