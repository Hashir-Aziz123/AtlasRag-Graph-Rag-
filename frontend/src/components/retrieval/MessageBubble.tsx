'use client';

import React from 'react';
import { Message } from '@/types/chat';
import { User, Network, AlertCircle, Sparkles, Waypoints } from 'lucide-react';

interface MessageBubbleProps {
    message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === 'user';

    if (isUser) {
        return (
            <div className="flex w-full justify-end mb-6">
                <div className="flex gap-4 max-w-[80%] items-start">
                    <div className="flex flex-col items-end gap-1">
                        <span className="text-xs font-medium text-slate-500 px-1">You</span>
                        <div className="bg-slate-900 text-white px-5 py-3.5 rounded-2xl rounded-tr-sm shadow-sm whitespace-pre-wrap text-sm leading-relaxed">
                            {message.content}
                        </div>
                    </div>
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center mt-5">
                        <User className="w-4 h-4 text-slate-600" />
                    </div>
                </div>
            </div>
        );
    }

    // Graph Intelligence rendering
    return (
        <div className="flex w-full justify-start mb-6">
            <div className="flex gap-4 max-w-[85%] items-start">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-50 border border-blue-100 flex items-center justify-center mt-5">
                    <Network className="w-4 h-4 text-blue-600" />
                </div>
                <div className="flex flex-col items-start gap-1 w-full">
                    <span className="text-xs font-medium text-slate-500 px-1">Graph Intelligence</span>
                    
                    <div className={`
                        relative px-5 py-4 rounded-2xl rounded-tl-sm text-sm leading-relaxed w-full shadow-sm border
                        ${message.isError 
                            ? 'bg-red-50 border-red-200 text-red-900' 
                            : 'bg-white border-slate-200 text-slate-800'
                        }
                    `}>
                        {message.isLoading ? (
                            <div className="flex flex-col gap-2 w-full animate-pulse">
                                <div className="h-4 bg-slate-100 rounded w-3/4"></div>
                                <div className="h-4 bg-slate-100 rounded w-1/2"></div>
                                <div className="flex items-center gap-2 mt-3 text-slate-400 text-xs font-medium">
                                    <Sparkles className="w-3 h-3" />
                                    Traversing knowledge graph...
                                </div>
                            </div>
                        ) : message.isError ? (
                            <div className="flex items-start gap-3">
                                <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                                <span>{message.content}</span>
                            </div>
                        ) : (
                            <div className="whitespace-pre-wrap flex flex-col gap-3">
                                {message.content}
                            </div>
                        )}

                        {/* Routing Intent Transparency Badge */}
                        {!message.isLoading && !message.isError && message.routed_intent && (
                            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-1.5 text-xs font-medium text-slate-400 uppercase tracking-wider">
                                <Waypoints className="w-3.5 h-3.5 text-slate-400" />
                                Routed via: <span className="text-blue-600">{message.routed_intent}</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}