import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react';
import Sidebar from '../src/components/Sidebar';

describe('Sidebar Component', () => {
  const mockConversations = [
    { id: 1, name: 'Alice', lastMessage: 'Hey there', updatedAt: '2023-01-01T00:00:00Z' },
    { id: 2, name: 'Bob', lastMessage: 'How are you?', updatedAt: '2023-01-02T00:00:00Z' },
    { id: 3, name: 'Charlie', lastMessage: null, updatedAt: null },
  ];

  test('renders conversation list', () => {
    const onSelect = jest.fn();
    const onCreateNew = jest.fn();
    render(
      <Sidebar
        conversations={mockConversations}
        onSelect={onSelect}
        onCreateNew={onCreateNew}
      />
    );
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('Charlie')).toBeInTheDocument();
  });

  test('calls onSelect when a conversation is clicked', () => {
    const onSelect = jest.fn();
    const onCreateNew = jest.fn();
    render(
      <Sidebar
        conversations={mockConversations}
        onSelect={onSelect}
        onCreateNew={onCreateNew}
      />
    );
    fireEvent.click(screen.getByText('Alice'));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  test('calls onCreateNew when New button clicked', () => {
    const onSelect = jest.fn();
    const onCreateNew = jest.fn();
    render(
      <Sidebar
        conversations={mockConversations}
        onSelect={onSelect}
        onCreateNew={onCreateNew}
      />
    );
    fireEvent.click(screen.getByText('+ New'));
    expect(onCreateNew).toHaveBeenCalled();
  });

  test('filters conversations based on search', () => {
    const onSelect = jest.fn();
    const onCreateNew = jest.fn();
    render(
      <Sidebar
        conversations={mockConversations}
        onSelect={onSelect}
        onCreateNew={onCreateNew}
      />
    );
    const searchInput = screen.getByPlaceholderText('Search conversations...');
    fireEvent.change(searchInput, { target: { value: 'Ali' } });
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.queryByText('Bob')).toBeNull();
  });

  test('shows "No messages yet" when lastMessage is null', () => {
    const onSelect = jest.fn();
    const onCreateNew = jest.fn();
    render(
      <Sidebar
        conversations={mockConversations}
        onSelect={onSelect}
        onCreateNew={onCreateNew}
      />
    );
    // Charlie has no lastMessage
    const charlieItem = screen.getByText('Charlie').closest('li');
    expect(charlieItem).toHaveTextContent('No messages yet');
  });

  test('displays empty state when no conversations', () => {
    const onSelect = jest.fn();
    const onCreateNew = jest.fn();
    render(
      <Sidebar
        conversations={[]}
        onSelect={onSelect}
        onCreateNew={onCreateNew}
      />
    );
    expect(screen.queryByRole('listitem')).toBeNull();
  });
});