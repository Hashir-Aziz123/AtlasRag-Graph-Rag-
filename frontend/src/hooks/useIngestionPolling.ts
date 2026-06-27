import { useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ingestionApi } from '@/lib/api';
import { useIngestion } from '@/contexts/IngestionContext';
import { UploadResponse } from '@/types/api';

export const useUploadDocument = () => {
    const { addTask } = useIngestion();

    return useMutation({
        mutationFn: (file: File) => ingestionApi.uploadDocument(file),
        onSuccess: (data: UploadResponse) => {
            // Push the Celery task ID into the global context so any component 
            // mounted anywhere can track its execution state.
            addTask(data.task_id);
        },
    });
};

export const useTaskStatus = (taskId: string) => {
    const { removeTask } = useIngestion();
    const queryClient = useQueryClient();

    const query = useQuery({
        queryKey: ['taskStatus', taskId],
        queryFn: () => ingestionApi.getTaskStatus(taskId),
        // Poll every 2 seconds. In React Query v5, this function receives the Query object.
        refetchInterval: (query) => {
            const status = query.state.data?.status;
            if (status === 'SUCCESS' || status === 'FAILURE') {
                return false;
            }
            return 2000;
        },
    });

    // Cleanup Effect: When the task reaches a terminal state, keep the status cached 
    // for display purposes, but remove the ID from the active polling context.
    useEffect(() => {
        const status = query.data?.status;
        if (status === 'SUCCESS' || status === 'FAILURE') {
            const timer = setTimeout(() => {
                removeTask(taskId);
                
                // If the ingestion succeeded, invalidate the document list query 
                // to force the UI to fetch the newly ingested document.
                if (status === 'SUCCESS') {
                    queryClient.invalidateQueries({ queryKey: ['documents'] });
                }
            }, 3000); 

            return () => clearTimeout(timer);
        }
    }, [query.data?.status, taskId, removeTask, queryClient]);

    return query;
};