/**
 * Chat Store - Zustand
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ChatMessage, Chunk, RoutingMetadata } from '@/types/api';

export interface ThinkingState {
  isThinking: boolean;
  currentStep: string;
  steps: string[];
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
}

interface ChatState {
  // Current session
  messages: ChatMessage[];
  chunks: Chunk[];
  routingMetadata: RoutingMetadata | null;
  isLoading: boolean;
  error: string | null;
  thinking: ThinkingState;
  streamingContent: string;

  // History (persisted)
  conversations: Conversation[];

  // Actions
  addMessage: (message: ChatMessage) => void;
  updateLastAssistantMessage: (content: string) => void;
  setChunks: (chunks: Chunk[]) => void;
  setRoutingMetadata: (metadata: RoutingMetadata | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setThinking: (thinking: Partial<ThinkingState>) => void;
  addThinkingStep: (step: string) => void;
  setStreamingContent: (content: string) => void;
  clearChat: () => void;
  resetThinking: () => void;
  saveCurrentConversation: () => void;
  loadConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  startNewChat: () => void;
}

const initialThinking: ThinkingState = {
  isThinking: false,
  currentStep: '',
  steps: [],
};

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      chunks: [],
      routingMetadata: null,
      isLoading: false,
      error: null,
      thinking: initialThinking,
      streamingContent: '',
      conversations: [],

      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),

      updateLastAssistantMessage: (content) =>
        set((state) => {
          const messages = [...state.messages];
          const lastIndex = messages.length - 1;
          if (lastIndex >= 0 && messages[lastIndex].role === 'assistant') {
            messages[lastIndex] = { ...messages[lastIndex], content };
          }
          return { messages };
        }),

      setChunks: (chunks) => set({ chunks }),

      setRoutingMetadata: (metadata) => set({ routingMetadata: metadata }),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      setThinking: (thinking) =>
        set((state) => ({
          thinking: { ...state.thinking, ...thinking },
        })),

      addThinkingStep: (step) =>
        set((state) => ({
          thinking: {
            ...state.thinking,
            currentStep: step,
            steps: [...state.thinking.steps, step],
          },
        })),

      setStreamingContent: (content) => set({ streamingContent: content }),

      saveCurrentConversation: () => {
        const { messages, conversations } = get();
        if (messages.length === 0) return;
        const firstUserMsg = messages.find((m) => m.role === 'user');
        const title = firstUserMsg
          ? firstUserMsg.content.slice(0, 50) + (firstUserMsg.content.length > 50 ? '…' : '')
          : 'Cuộc hội thoại mới';
        const id = Date.now().toString();
        const newConv: Conversation = { id, title, messages, createdAt: Date.now() };
        set({ conversations: [newConv, ...conversations].slice(0, 50) });
      },

      loadConversation: (id) => {
        const { conversations } = get();
        const conv = conversations.find((c) => c.id === id);
        if (conv) {
          set({
            messages: conv.messages,
            chunks: [],
            routingMetadata: null,
            error: null,
            thinking: initialThinking,
            streamingContent: '',
          });
        }
      },

      deleteConversation: (id) =>
        set((state) => ({ conversations: state.conversations.filter((c) => c.id !== id) })),

      startNewChat: () => {
        const { messages, saveCurrentConversation } = get();
        if (messages.length > 0) saveCurrentConversation();
        set({
          messages: [],
          chunks: [],
          routingMetadata: null,
          error: null,
          thinking: initialThinking,
          streamingContent: '',
        });
      },

      clearChat: () =>
        set({
          messages: [],
          chunks: [],
          routingMetadata: null,
          error: null,
          thinking: initialThinking,
          streamingContent: '',
        }),

      resetThinking: () =>
        set({
          thinking: initialThinking,
          streamingContent: '',
        }),
    }),
    {
      name: 'chat-history',
      partialize: (state) => ({ conversations: state.conversations }),
    }
  )
);
