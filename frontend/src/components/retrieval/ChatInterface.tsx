'use client';

import React, { useRef, useEffect } from 'react';
import { Network, Search } from 'lucide-react';
import { useChatSession } from '@/hooks/useChatSession';
import { MessageBubble } from '@/components/retrieval/MessageBubble';
import { QueryInput } from '@/components/retrieval/QueryInput';

export function ChatInterface() {
    const { messages, sendMessage, isThinking } = useChatSession();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to the bottom when the message array mutates
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    return (
        <div className="flex flex-col h-full w-full bg-slate-50 relative">
            
            {/* Scrollable Message History Container */}
            <div className="flex-1 overflow-y-auto px-4 py-8 custom-scrollbar">
                <div className="max-w-4xl mx-auto w-full flex flex-col justify-end min-h-full">
                    {messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-slate-500 my-auto pb-20">
                            <div className="w-16 h-16 bg-white border border-slate-200 rounded-2xl flex items-center justify-center mb-6 shadow-sm">
                                <Network className="w-8 h-8 text-blue-600" />
                            </div>
                            <h2 className="text-xl font-semibold text-slate-800 tracking-tight mb-2">
                                Graph RAG Intelligence
                            </h2>
                            <p className="text-sm text-center max-w-md text-slate-500 mb-8 leading-relaxed">
                                Query the federated knowledge base. The system will route your intent, traverse the Neo4j topology, and synthesize context from Qdrant vectors.
                            </p>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
                                <div className="flex items-start gap-3 p-4 bg-white border border-slate-200 rounded-xl cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all" onClick={() => sendMessage("What acquisitions or mergers are mentioned in the documents?")}>
                                    <Search className="w-4 h-4 mt-0.5 text-blue-600" />
                                    <span className="text-sm font-medium text-slate-700">Analyze acquisitions and mergers</span>
                                </div>
                                <div className="flex items-start gap-3 p-4 bg-white border border-slate-200 rounded-xl cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all" onClick={() => sendMessage("Identify key products and infrastructure technologies.")}>
                                    <Search className="w-4 h-4 mt-0.5 text-blue-600" />
                                    <span className="text-sm font-medium text-slate-700">Map product infrastructure</span>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col w-full pb-4">
                            {messages.map((msg) => (
                                <MessageBubble key={msg.id} message={msg} />
                            ))}
                            {/* Invisible anchor for auto-scrolling */}
                            <div ref={messagesEndRef} className="h-1" />
                        </div>
                    )}
                </div>
            </div>

            {/* Input Container (Anchored to bottom) */}
            <div className="w-full bg-gradient-to-t from-slate-50 via-slate-50 to-transparent pt-6 pb-4 px-4 z-10 shrink-0">
                <div className="max-w-4xl mx-auto w-full">
                    <QueryInput onSendMessage={sendMessage} isThinking={isThinking} />
                </div>
            </div>
            
        </div>
    );
}