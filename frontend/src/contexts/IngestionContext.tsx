'use client';

import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';

interface IngestionState {
    activeTaskIds: string[];
    addTask: (taskId: string) => void;
    removeTask: (taskId: string) => void;
}

const IngestionContext = createContext<IngestionState | undefined>(undefined);

export const IngestionProvider = ({ children }: { children: ReactNode }) => {
    const [activeTaskIds, setActiveTaskIds] = useState<string[]>([]);

    const addTask = useCallback((taskId: string) => {
        setActiveTaskIds((prev) => {
            // Prevent pushing duplicate task IDs if a user manages to double-click an upload
            if (prev.includes(taskId)) return prev;
            return [...prev, taskId];
        });
    }, []);

    const removeTask = useCallback((taskId: string) => {
        setActiveTaskIds((prev) => prev.filter((id) => id !== taskId));
    }, []);

    return (
        <IngestionContext.Provider value={{ activeTaskIds, addTask, removeTask }}>
            {children}
        </IngestionContext.Provider>
    );
};

export const useIngestion = (): IngestionState => {
    const context = useContext(IngestionContext);
    if (!context) {
        throw new Error('useIngestion must be used within an IngestionProvider');
    }
    return context;
};