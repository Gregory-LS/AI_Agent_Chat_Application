import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from '../src/components/Sidebar';

describe('Sidebar component', () => {
  const mockConversations = [
    {
      id: '1',
      title: 'Project Alpha',
      participants: ['Alice', 'Bob'],
      lastMessage: 'Let's meet tomorrow',
      timestamp: 1700000000,
    },
    {
      id: '2',
      title: 'Design Review',
      participants: ['Charlie', 'Diana'],
      lastMessage: 'Looks great!',
      timestamp: 1700000100,
    },
    {
      id: '3',
      title: 'Random Chat',
      participants: ['Eve', 'Frank'],
      lastMessage: 'How are you?',
      timestamp: 1700000200,
    },
  ];

  const mockOnSelect = jest.fn();

  beforeEach(() => {
    mockOnSelect.mockClear();
  });

  it('renders all conversations when no search query', () => {
    render(
      <Sidebar
        conversations={mockConversations}
        onSelectConversation={mockOnSelect}
        selectedConversationId={undefined}
      />
    );

    expect(screen.getByText('Project Alpha')).toBeInTheDocument();
    expect(screen.getByText('Design Review')).toBeInTheDocument();
    expect(screen.getByText('Random Chat')).toBeInTheDocument();
  });

  it('filters conversations by title', () => {
    render(
      <Sidebar
        conversations={mockConversations}
        onSelectConversation={mockOnSelect}
        selectedConversationId={undefined}
      />
    );

    const searchInput = screen.getByLabelText('Search conversations');
    fireEvent.change(searchInput, { target: { value: 'alpha' } });

    expect(screen.getByText('Project Alpha')).toBeInTheDocument();
    expect(screen.queryByText('Design Review')).not.toBeInTheDocument();
    expect(screen.queryByText('Random Chat')).not.toBeInTheDocument();
  });

  it('filters conversations by participant name', () => {
    render(
      <Sidebar
        conversations={mockConversations}
        onSelectConversation={mockOnSelect}
        selectedConversationId={undefined}
      />
    );

    const searchInput = screen.getByLabelText('Search conversations');
    fireEvent.change(searchInput, { target: { value: 'charlie' } });

    expect(screen.getByText('Design Review')).toBeInTheDocument();
    expect(screen.queryByText('Project Alpha')).not.toBeInTheDocument();
    expect(screen.queryByText('Random Chat')).not.toBeInTheDocument();
  });

  it('shows no results message when no matches', () => {
    render(
      <Sidebar
        conversations={mockConversations}
        onSelectConversation={mockOnSelect}
        selectedConversationId={undefined}
      />
    );

    const searchInput = screen.getByLabelText('Search conversations');
    fireEvent.change(searchInput, { target: { value: 'zzz' } });

    expect(screen.getByText('No conversations found')).toBeInTheDocument();
  });

  it('clears search when clear button is clicked', () => {
    render(
      <Sidebar
        conversations={mockConversations}
        onSelectConversation={mockOnSelect}
        selectedConversationId={undefined}
      />
    );

    const searchInput = screen.getByLabelText('Search conversations');
    fireEvent.change(searchInput, { target: { value: 'alpha' } });
    expect(screen.getByText('Project Alpha')).toBeInTheDocument();

    const clearButton = screen.getByLabelText('Clear search');
    fireEvent.click(clearButton);

    expect(screen.getByText('Project Alpha')).toBeInTheDocument();
    expect(screen.getByText('Design Review')).toBeInTheDocument();
    expect(screen.getByText('Random Chat')).toBeInTheDocument();
    expect(searchInput).toHaveValue('');
  });

  it('calls onSelectConversation when a conversation is clicked', () => {
    render(
      <Sidebar
        conversations={mockConversations}
        onSelectConversation={mockOnSelect}
        selectedConversationId={undefined}
      />
    );

    fireEvent.click(screen.getByText('Project Alpha'));
    expect(mockOnSelect).toHaveBeenCalledWith('1');
  });

  it('highlights the selected conversation', () => {
    render(
      <Sidebar
        conversations={mockConversations}
        onSelectConversation={mockOnSelect}
        selectedConversationId="2"
      />
    );

    const selectedItem = screen.getByText('Design Review').closest('li');
    expect(selectedItem).toHaveClass('selected');
  });
});
