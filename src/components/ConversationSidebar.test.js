import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ConversationSidebar from './ConversationSidebar';

beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.restoreAllMocks();
});

test('renders conversations from API', async () => {
  const mockConversations = [
    { id: 1, title: 'Chat A' },
    { id: 2, title: 'Chat B' },
  ];
  global.fetch.mockResolvedValueOnce({
    json: async () => mockConversations,
  });

  render(<ConversationSidebar />);

  await waitFor(() => {
    expect(screen.getByText('Chat A')).toBeInTheDocument();
    expect(screen.getByText('Chat B')).toBeInTheDocument();
  });
});

test('highlights active conversation on click', async () => {
  const mockConversations = [
    { id: 1, title: 'Chat A' },
    { id: 2, title: 'Chat B' },
  ];
  global.fetch.mockResolvedValueOnce({
    json: async () => mockConversations,
  });

  const onSelect = jest.fn();
  render(<ConversationSidebar onSelectConversation={onSelect} />);

  await waitFor(() => screen.getByText('Chat A'));
  const chatA = screen.getByText('Chat A');
  fireEvent.click(chatA);

  expect(chatA.closest('li')).toHaveClass('active');
  expect(onSelect).toHaveBeenCalledWith(1);
});

test('creates a new conversation', async () => {
  global.fetch.mockResolvedValueOnce({
    json: async () => [{ id: 1, title: 'Existing' }],
  });

  render(<ConversationSidebar />);

  await waitFor(() => screen.getByText('Existing'));

  const input = screen.getByPlaceholderText('New conversation title...');
  fireEvent.change(input, { target: { value: 'New Chat' } });

  global.fetch.mockResolvedValueOnce({
    json: async () => ({ id: 2, title: 'New Chat' }),
  });

  const createButton = screen.getByText('+');
  fireEvent.click(createButton);

  await waitFor(() => {
    expect(screen.getByText('New Chat')).toBeInTheDocument();
  });
});

test('deletes a conversation with confirmation', async () => {
  const mockConversations = [
    { id: 1, title: 'Chat A' },
    { id: 2, title: 'Chat B' },
  ];
  global.fetch.mockResolvedValueOnce({
    json: async () => mockConversations,
  });

  window.confirm = jest.fn(() => true);

  render(<ConversationSidebar />);

  await waitFor(() => screen.getByText('Chat A'));

  const deleteButtons = screen.getAllByText('×');
  fireEvent.click(deleteButtons[0]);

  expect(window.confirm).toHaveBeenCalled();

  global.fetch.mockResolvedValueOnce({});

  await waitFor(() => {
    expect(screen.queryByText('Chat A')).not.toBeInTheDocument();
  });
});

test('does not delete if confirmation is cancelled', async () => {
  const mockConversations = [
    { id: 1, title: 'Chat A' },
  ];
  global.fetch.mockResolvedValueOnce({
    json: async () => mockConversations,
  });

  window.confirm = jest.fn(() => false);

  render(<ConversationSidebar />);

  await waitFor(() => screen.getByText('Chat A'));

  const deleteButton = screen.getByText('×');
  fireEvent.click(deleteButton);

  expect(window.confirm).toHaveBeenCalled();
  expect(screen.getByText('Chat A')).toBeInTheDocument();
});
