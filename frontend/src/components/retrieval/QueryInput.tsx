'use client';

import React, { useState, useRef, KeyboardEvent, useEffect } from 'react';
import { ArrowUp, Loader2 } from 'lucide-react';

interface QueryInputProps {
    onSendMessage: (message: string) => void;
    isThinking: boolean;
}

export function QueryInput({ onSendMessage, isThinking }: QueryInputProps) {
    const [input, setInput] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize the textarea as the user types, up to a maximum height
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'inherit';
            const scrollHeight = textareaRef.current.scrollHeight;
            textareaRef.current.style.height = `${Math.min(scrollHeight, 200)}px`;
        }
    }, [input]);

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const handleSubmit = () => {
        if (input.trim() && !isThinking) {
            onSendMessage(input);
            setInput('');
            
            // Reset height after submission
            if (textareaRef.current) {
                textareaRef.current.style.height = 'inherit';
            }
        }
    };

    return (
        <div className="w-full max-w-3xl mx-auto p-4 bg-transparent">
            <div className="relative flex items-end w-full bg-white border border-slate-300 rounded-2xl shadow-sm focus-within:ring-2 focus-within:ring-slate-900 focus-within:border-transparent transition-all overflow-hidden">
                <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isThinking}
                    placeholder="Query the knowledge graph..."
                    className="w-full max-h-[200px] min-h-[56px] py-4 pl-4 pr-14 bg-transparent border-none resize-none focus:outline-none text-slate-900 placeholder:text-slate-400 disabled:opacity-50 disabled:cursor-not-allowed custom-scrollbar"
                    rows={1}
                />
                
                <div className="absolute right-2 bottom-2">
                    <button
                        onClick={handleSubmit}
                        disabled={!input.trim() || isThinking}
                        className={`
                            p-2 rounded-xl flex items-center justify-center transition-all duration-200
                            ${!input.trim() || isThinking
                                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                                : 'bg-slate-900 text-white hover:bg-slate-800 hover:shadow-md'
                            }
                        `}
                        aria-label="Send query"
                    >
                        {isThinking ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <ArrowUp className="w-5 h-5" />
                        )}
                    </button>
                </div>
            </div>
            
            <div className="mt-2 text-center">
                <p className="text-xs text-slate-400">
                    Graph Intelligence can make mistakes. Verify critical claims against source documents.
                </p>
            </div>
        </div>
    );
}