'use client';

import React from 'react';
import { Loader2, CheckCircle2, XCircle, Clock, AlertCircle } from 'lucide-react';
import { useTaskStatus } from '@/hooks/useIngestionPolling';
import { TaskStatus } from '@/types/api';

interface TaskMonitorProps {
    taskId: string;
}

export function TaskMonitor({ taskId }: TaskMonitorProps) {
    const { data, isError } = useTaskStatus(taskId);

    // Fallback to PENDING while the initial network request resolves
    const status: TaskStatus = data?.status || 'PENDING';
    
    // UI configuration map to keep the render function clean
    const statusConfig = {
        PENDING: {
            icon: Clock,
            color: 'text-slate-500',
            bgColor: 'bg-slate-100',
            barColor: 'bg-slate-300',
            barWidth: 'w-1/4',
            label: 'Queued...',
            spin: false
        },
        STARTED: {
            icon: Loader2,
            color: 'text-blue-600',
            bgColor: 'bg-blue-50',
            barColor: 'bg-blue-500 animate-pulse',
            barWidth: 'w-2/3',
            label: 'Extracting Knowledge...',
            spin: true
        },
        SUCCESS: {
            icon: CheckCircle2,
            color: 'text-emerald-600',
            bgColor: 'bg-emerald-50',
            barColor: 'bg-emerald-500',
            barWidth: 'w-full',
            label: 'Ingestion Complete',
            spin: false
        },
        FAILURE: {
            icon: XCircle,
            color: 'text-red-600',
            bgColor: 'bg-red-50',
            barColor: 'bg-red-500',
            barWidth: 'w-full',
            label: 'Pipeline Failure',
            spin: false
        }
    };

    const config = statusConfig[status];
    const Icon = config.icon;

    if (isError) {
        return (
            <div className="w-full p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3 shadow-sm">
                <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                <div className="flex flex-col overflow-hidden">
                    <span className="text-sm font-medium text-red-800">Connection Dropped</span>
                    <span className="text-xs text-red-600 truncate">Failed to monitor task status.</span>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full p-3 bg-white border border-slate-200 rounded-lg shadow-sm transition-all duration-300">
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <div className={`p-1.5 rounded-md ${config.bgColor}`}>
                        <Icon className={`w-4 h-4 ${config.color} ${config.spin ? 'animate-spin' : ''}`} />
                    </div>
                    <span className="text-sm font-medium text-slate-700">
                        {config.label}
                    </span>
                </div>
                {/* Render the first segment of the UUID to give the user a unique identifier without cluttering the UI */}
                <span className="text-xs text-slate-400 font-mono">
                    {taskId.split('-')[0]}
                </span>
            </div>
            
            <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div 
                    className={`h-full rounded-full transition-all duration-500 ease-out ${config.barWidth} ${config.barColor}`}
                />
            </div>
            
            {data?.result && (
                <p className={`mt-2 text-xs font-medium truncate ${status === 'FAILURE' ? 'text-red-600' : 'text-slate-500'}`}>
                    {data.result}
                </p>
            )}
        </div>
    );
}