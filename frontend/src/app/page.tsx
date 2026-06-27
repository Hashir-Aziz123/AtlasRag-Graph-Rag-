import React from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { MessageSquare } from 'lucide-react';

export default function Home() {
    return (
        <div className="flex h-screen w-full bg-white overflow-hidden">
            {/* Left Panel: Ingestion & Knowledge Base Management */}
            <Sidebar />

            {/* Main Canvas: Retrieval & Intelligence Interface (Phase 3 Placeholder) */}
            <main className="flex-1 flex flex-col items-center justify-center bg-slate-50 relative">
                <div className="flex flex-col items-center text-slate-400">
                    <div className="p-4 bg-white rounded-full shadow-sm border border-slate-100 mb-4">
                        <MessageSquare className="w-8 h-8 text-slate-300" />
                    </div>
                    <h1 className="text-xl font-semibold text-slate-600 tracking-tight">
                        Graph Intelligence Canvas
                    </h1>
                    <p className="text-sm mt-2 text-slate-500 max-w-sm text-center">
                        Upload documents in the sidebar to populate the knowledge graph. 
                        The retrieval interface will be constructed here.
                    </p>
                </div>
            </main>
        </div>
    );
}