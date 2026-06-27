'use client';

import React, { useState, useCallback, useRef } from 'react';
import { UploadCloud, FileText, Loader2, X } from 'lucide-react';
import { useUploadDocument } from '@/hooks/useIngestionPolling';

export function UploadDropzone() {
    const [isDragging, setIsDragging] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    
    const { mutate: uploadDocument, isPending, isError } = useUploadDocument();

    const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files && files.length > 0 && files[0].type === 'application/pdf') {
            setSelectedFile(files[0]);
        }
    }, []);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setSelectedFile(e.target.files[0]);
        }
    };

    const handleExecute = () => {
        if (!selectedFile) return;
        
        uploadDocument(selectedFile, {
            onSuccess: () => {
                // Clear the local state so the user can upload another document
                // while the background Celery task processes the first one.
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
            }
        });
    };

    const clearSelection = (e: React.MouseEvent) => {
        e.stopPropagation();
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    return (
        <div className="flex flex-col gap-4 w-full">
            <div 
                onClick={() => !isPending && fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`
                    relative flex flex-col items-center justify-center w-full p-6 
                    border-2 border-dashed rounded-xl cursor-pointer transition-all duration-200
                    ${isPending ? 'opacity-50 cursor-not-allowed border-slate-200 bg-slate-50' : ''}
                    ${isDragging ? 'border-slate-600 bg-slate-100' : 'border-slate-300 hover:border-slate-400 bg-white hover:bg-slate-50'}
                `}
            >
                <input 
                    type="file" 
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    accept=".pdf"
                    className="hidden"
                    disabled={isPending}
                />
                
                {!selectedFile ? (
                    <>
                        <div className="p-3 bg-slate-100 rounded-full mb-3">
                            <UploadCloud className="w-6 h-6 text-slate-600" />
                        </div>
                        <p className="text-sm font-medium text-slate-700">
                            Click or drag to upload
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                            PDF documents only (max 50MB)
                        </p>
                    </>
                ) : (
                    <div className="flex items-center justify-between w-full p-3 bg-white border border-slate-200 rounded-lg shadow-sm">
                        <div className="flex items-center gap-3 overflow-hidden">
                            <div className="p-2 bg-blue-50 rounded-md">
                                <FileText className="w-5 h-5 text-blue-600" />
                            </div>
                            <div className="flex flex-col truncate">
                                <span className="text-sm font-medium text-slate-700 truncate">
                                    {selectedFile.name}
                                </span>
                                <span className="text-xs text-slate-500">
                                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                </span>
                            </div>
                        </div>
                        {!isPending && (
                            <button 
                                onClick={clearSelection}
                                className="p-1 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-600 transition-colors"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                )}
            </div>

            <button
                onClick={handleExecute}
                disabled={!selectedFile || isPending}
                className={`
                    flex items-center justify-center gap-2 w-full py-2.5 px-4 
                    rounded-lg text-sm font-medium transition-all
                    ${!selectedFile || isPending 
                        ? 'bg-slate-100 text-slate-400 cursor-not-allowed' 
                        : 'bg-slate-900 text-white hover:bg-slate-800 shadow-sm hover:shadow'
                    }
                `}
            >
                {isPending ? (
                    <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Dispatching to Pipeline...
                    </>
                ) : (
                    'Execute Ingestion'
                )}
            </button>

            {isError && (
                <p className="text-xs text-red-600 text-center font-medium">
                    Network error: Failed to dispatch document.
                </p>
            )}
        </div>
    );
}