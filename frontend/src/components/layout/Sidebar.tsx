'use client';

import React from 'react';
import { Database, Activity, Library } from 'lucide-react';
import { useIngestion } from '@/contexts/IngestionContext';
import { UploadDropzone } from '@/components/ingestion/UploadDropzone';
import { TaskMonitor } from '@/components/ingestion/TaskMonitor';
import { DocumentList } from '@/components/ingestion/DocumentList';

export function Sidebar() {
    const { activeTaskIds } = useIngestion();

    return (
        <aside className="w-96 h-screen flex flex-col bg-slate-50/50 border-r border-slate-200 shrink-0">
            {/* Header */}
            <div className="p-6 border-b border-slate-200 bg-white">
                <div className="flex items-center gap-2 text-slate-900">
                    <Database className="w-5 h-5" />
                    <h2 className="text-lg font-semibold tracking-tight">Knowledge Base</h2>
                </div>
                <p className="text-sm text-slate-500 mt-1">
                    Manage graph ingestion and vectors.
                </p>
            </div>

            {/* Scrollable Content Area */}
            <div className="flex-1 overflow-y-auto overflow-x-hidden flex flex-col gap-6 p-6 custom-scrollbar">
                
                {/* Upload Section */}
                <section className="flex flex-col gap-3">
                    <UploadDropzone />
                </section>

                {/* Active Processes Section */}
                {activeTaskIds.length > 0 && (
                    <section className="flex flex-col gap-3 animate-in fade-in slide-in-from-top-4 duration-300">
                        <div className="flex items-center gap-2 text-slate-800 px-1">
                            <Activity className="w-4 h-4 text-blue-600" />
                            <h3 className="text-sm font-semibold">Active Pipeline</h3>
                            <span className="ml-auto bg-blue-100 text-blue-700 text-xs font-bold px-2 py-0.5 rounded-full">
                                {activeTaskIds.length}
                            </span>
                        </div>
                        <div className="flex flex-col gap-3">
                            {activeTaskIds.map((id) => (
                                <TaskMonitor key={id} taskId={id} />
                            ))}
                        </div>
                    </section>
                )}

                {/* Document Library Section */}
                <section className="flex flex-col gap-3 mt-4 border-t border-slate-200 pt-6">
                    <div className="flex items-center gap-2 text-slate-800 px-1">
                        <Library className="w-4 h-4 text-slate-600" />
                        <h3 className="text-sm font-semibold">Indexed Documents</h3>
                    </div>
                    
                    <DocumentList />
                </section>

            </div>
        </aside>
    );
}