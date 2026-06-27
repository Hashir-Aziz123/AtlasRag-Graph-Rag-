export type MessageRole = 'user' | 'assistant';

export interface Message {
    id: string;
    role: MessageRole;
    content: string;
    
    // Optional metadata surfaced from the backend for UI transparency
    routed_intent?: string;
    
    // UI state flags specific to the assistant's responses
    isLoading?: boolean;
    isError?: boolean;
}