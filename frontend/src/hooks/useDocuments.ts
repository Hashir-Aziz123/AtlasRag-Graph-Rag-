import { useQuery } from '@tanstack/react-query';
import { ingestionApi } from '@/lib/api';
import { IngestedDocument } from '@/types/api';

export const useDocuments = () => {
    return useQuery<IngestedDocument[], Error>({
        queryKey: ['documents'],
        queryFn: ingestionApi.getDocuments,
        // Data is considered fresh for 5 minutes. 
        // It will only refetch early if manually invalidated (e.g., via our upload success hook).
        staleTime: 5 * 60 * 1000, 
    });
};