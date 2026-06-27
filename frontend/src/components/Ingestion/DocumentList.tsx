'use client';

import React from 'react';
import { FileText, Loader2, AlertCircle, Database, Calendar } from 'lucide-react';
import { useDocuments } from '@/hooks/useDocuments';

const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'Unknown date';
    try {
        return new Intl.DateTimeFormat('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        }).format(new Date(dateString));
    } catch {
        return 'Invalid date';
    }
};

export function DocumentList() {
    const { data: documents, isLoading, isError } = useDocuments();

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center p-6 text-slate-400 border border-slate-200 border-dashed rounded-lg bg-slate-50/50">
                <Loader2 className="w-5 h-5 animate-spin mb-2" />
                <span className="text-sm font-medium">Loading library...</span>
            </div>
        );
    }

    if (isError) {
        return (
            <div className="flex items-start gap-3 p-4 text-red-600 bg-red-50 border border-red-100 rounded-lg">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <div className="flex flex-col">
                    <span className="text-sm font-medium">Sync Failed</span>
                    <span className="text-xs text-red-500">Could not retrieve document history.</span>
                </div>
            </div>
        );
    }

    if (!documents || documents.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-6 text-slate-400 border border-slate-200 border-dashed rounded-lg bg-slate-50/50">
                <FileText className="w-6 h-6 mb-2 text-slate-300" />
                <span className="text-sm font-medium text-slate-500">No documents indexed</span>
                <span className="text-xs text-center mt-1">Upload a PDF above to populate the knowledge graph.</span>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-2">
            {documents.map((doc) => (
                <div 
                    key={doc.id} 
                    className="group flex flex-col gap-1.5 p-3 rounded-lg border border-transparent hover:border-slate-200 hover:bg-slate-50 transition-all duration-200"
                >
                    <div className="flex items-start gap-3">
                        <FileText className="w-4 h-4 mt-0.5 text-slate-400 group-hover:text-blue-500 transition-colors shrink-0" />
                        <div className="flex flex-col overflow-hidden w-full">
                            <span className="text-sm font-medium text-slate-700 truncate" title={doc.filename}>
                                {doc.filename}
                            </span>
                            
                            <div className="flex items-center gap-3 mt-1.5">
                                <div className="flex items-center gap-1 text-xs text-slate-500">
                                    <Database className="w-3 h-3" />
                                    <span>{doc.chunk_count} chunks</span>
                                </div>
                                <div className="flex items-center gap-1 text-xs text-slate-500">
                                    <Calendar className="w-3 h-3" />
                                    <span>{formatDate(doc.created_at)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}