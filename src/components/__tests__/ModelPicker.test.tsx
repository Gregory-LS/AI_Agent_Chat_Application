import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ModelPicker from '../ModelPicker';

beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.restoreAllMocks();
});

test('renders loading state initially', () => {
  (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {})); // never resolves
  render(<ModelPicker onSelect={jest.fn()} />);
  expect(screen.getByText('Loading models...')).toBeInTheDocument();
});

test('renders error state when fetch fails', async () => {
  (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));
  render(<ModelPicker onSelect={jest.fn()} />);
  await waitFor(() => {
    expect(screen.getByText('Error: Network error')).toBeInTheDocument();
  });
});

test('renders models and calls onSelect when a model is chosen', async () => {
  const models = [
    { id: '1', name: 'Model A' },
    { id: '2', name: 'Model B' },
  ];
  (global.fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => models,
  });
  const onSelect = jest.fn();
  render(<ModelPicker onSelect={onSelect} />);

  await waitFor(() => {
    expect(screen.getByText('Model A')).toBeInTheDocument();
    expect(screen.getByText('Model B')).toBeInTheDocument();
  });

  const select = screen.getByRole('combobox');
  await userEvent.selectOptions(select, '1');
  expect(onSelect).toHaveBeenCalledWith({ id: '1', name: 'Model A' });
});

test('renders dropdown with placeholder option', async () => {
  (global.fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => [],
  });
  render(<ModelPicker onSelect={jest.fn()} />);
  await waitFor(() => {
    expect(screen.getByText('-- Choose a model --')).toBeInTheDocument();
  });
});
