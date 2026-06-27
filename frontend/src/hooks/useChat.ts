import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { retrievalApi } from '@/lib/api';
import { Message } from '@/types/chat';

const generateId = (): string => {
    return typeof crypto !== 'undefined' && crypto.randomUUID 
        ? crypto.randomUUID() 
        : Math.random().toString(36).substring(2, 15);
};

export const useChat = () => {
    const [messages, setMessages] = useState<Message[]>([]);

    const chatMutation = useMutation({
        mutationFn: (query: string) => retrievalApi.queryKnowledgeBase({ query })
    });

    const sendMessage = useCallback((content: string) => {
        const trimmedContent = content.trim();
        if (!trimmedContent) return;

        const userMessageId = generateId();
        const assistantMessageId = generateId();

        const userMessage: Message = {
            id: userMessageId,
            role: 'user',
            content: trimmedContent,
        };

        const placeholderMessage: Message = {
            id: assistantMessageId,
            role: 'assistant',
            content: '',
            isLoading: true,
        };

        // Optimistically update the UI before the network request begins
        setMessages((prev) => [...prev, userMessage, placeholderMessage]);

        chatMutation.mutate(trimmedContent, {
            onSuccess: (data) => {
                setMessages((prev) => 
                    prev.map((msg) => 
                        msg.id === assistantMessageId 
                            ? { 
                                ...msg, 
                                content: data.answer, 
                                isLoading: false, 
                                routed_intent: data.routed_intent 
                              }
                            : msg
                    )
                );
            },
            onError: (error) => {
                setMessages((prev) => 
                    prev.map((msg) => 
                        msg.id === assistantMessageId 
                            ? { 
                                ...msg, 
                                content: 'A network anomaly disrupted the retrieval sequence. Please verify the backend connection and try again.', 
                                isLoading: false, 
                                isError: true 
                              }
                            : msg
                    )
                );
                console.error("Knowledge base query failed:", error);
            }
        });
    }, [chatMutation]);

    return {
        messages,
        sendMessage,
        isThinking: chatMutation.isPending
    };
};