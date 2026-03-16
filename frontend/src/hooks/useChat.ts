/**
 * useChat Hook - Handles chat logic with streaming support
 */

import { useCallback } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { sendChatMessageStream } from '@/lib/api';
import type { ChatMessage, StreamEvent, Chunk, RoutingMetadata } from '@/types/api';

export function useChat() {
  const {
    messages,
    chunks,
    routingMetadata,
    isLoading,
    error,
    thinking,
    streamingContent,
    conversations,
    addMessage,
    updateLastAssistantMessage,
    setChunks,
    setRoutingMetadata,
    setLoading,
    setError,
    setThinking,
    addThinkingStep,
    setStreamingContent,
    clearChat,
    resetThinking,
    startNewChat,
    loadConversation,
    deleteConversation,
  } = useChatStore();

  const sendMessage = useCallback(
    async (question: string, useAgent?: boolean | null) => {
      if (!question.trim() || isLoading) return;

      // Add user message
      const userMessage: ChatMessage = { role: 'user', content: question };
      addMessage(userMessage);

      setLoading(true);
      setError(null);
      resetThinking();
      setThinking({ isThinking: true });

      try {
        // Build history from existing messages (excluding the one we just added)
        const history = messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
        }));

        // Add placeholder assistant message for streaming
        addMessage({ role: 'assistant', content: '' });

        let currentContent = '';

        await sendChatMessageStream(
          {
            question,
            history,
            use_agent: useAgent,
          },
          (event: StreamEvent) => {
            switch (event.type) {
              case 'thinking':
                addThinkingStep(event.message);
                break;

              case 'routing':
                addThinkingStep(event.message);
                break;

              case 'chunks':
                setChunks(event.chunks as Chunk[]);
                setThinking({ isThinking: false });
                break;

              case 'token':
                currentContent = event.full_content;
                setStreamingContent(currentContent);
                updateLastAssistantMessage(currentContent);
                break;

              case 'metadata':
                setRoutingMetadata(event.routing_metadata as RoutingMetadata);
                break;

              case 'done':
                break;

              case 'error':
                setError(event.error);
                break;
            }
          }
        );
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);
      } finally {
        setLoading(false);
        setThinking({ isThinking: false });
      }
    },
    [
      messages,
      isLoading,
      addMessage,
      updateLastAssistantMessage,
      setChunks,
      setRoutingMetadata,
      setLoading,
      setError,
      setThinking,
      addThinkingStep,
      setStreamingContent,
      resetThinking,
    ]
  );

  return {
    messages,
    chunks,
    routingMetadata,
    isLoading,
    error,
    thinking,
    streamingContent,
    conversations,
    sendMessage,
    clearChat,
    startNewChat,
    loadConversation,
    deleteConversation,
  };
}
