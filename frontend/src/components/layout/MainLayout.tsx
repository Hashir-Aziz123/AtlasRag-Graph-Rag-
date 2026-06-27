'use client';

import React, { ReactNode } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';

interface MainLayoutProps {
    children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
    return (
        <div className="flex h-screen w-full bg-white overflow-hidden">
            {/* Persistent Global Sidebar */}
            <Sidebar />

            {/* Dynamic Page Content */}
            <main className="flex-1 relative bg-slate-50">
                {children}
            </main>
        </div>
    );
}