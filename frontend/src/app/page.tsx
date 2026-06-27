import React from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { ChatInterface } from '@/components/retrieval/ChatInterface';

export default function Home() {
    return (
        <MainLayout>
            <ChatInterface />
        </MainLayout>
    );
}