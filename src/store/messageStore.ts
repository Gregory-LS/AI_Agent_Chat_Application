import { create } from 'zustand';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: number;
}

interface MessageState {
  messages: Message[];
  addMessage: (message: Message) => void;
  deleteMessage: (id: string) => void;
  editMessage: (id: string, newContent: string) => void;
}

export const useMessageStore = create<MessageState>((set) => ({
  messages: [],
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  deleteMessage: (id) =>
    set((state) => ({ messages: state.messages.filter((m) => m.id !== id) })),
  editMessage: (id, newContent) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, content: newContent } : m
      ),
    })),
}));
