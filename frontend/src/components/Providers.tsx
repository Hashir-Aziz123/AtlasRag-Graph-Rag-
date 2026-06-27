'use client';

import { ReactNode, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { IngestionProvider } from '@/contexts/IngestionContext';

export function Providers({ children }: { children: ReactNode }) {
    // Instantiate QueryClient inside useState to ensure it is 
    // initialized exactly once per user session.
    const [queryClient] = useState(() => new QueryClient({
        defaultOptions: {
            queries: {
                refetchOnWindowFocus: false,
                retry: 1,
            },
        },
    }));

    return (
        <QueryClientProvider client={queryClient}>
            <IngestionProvider>
                {children}
            </IngestionProvider>
        </QueryClientProvider>
    );
}