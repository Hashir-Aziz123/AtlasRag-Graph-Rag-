import axios from 'axios';
import { 
    UploadResponse, 
    TaskStatusResponse, 
    QueryRequest, 
    QueryResponse,
    IngestedDocument
} from '@/types/api';

const apiClient = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const ingestionApi = {
    uploadDocument: async (file: File): Promise<UploadResponse> => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await apiClient.post<UploadResponse>('/api/v1/ingest/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        
        return response.data;
    },

    getTaskStatus: async (taskId: string): Promise<TaskStatusResponse> => {
        const response = await apiClient.get<TaskStatusResponse>(`/api/v1/ingest/status/${taskId}`);
        return response.data;
    },

    getDocuments: async (): Promise<IngestedDocument[]> => {
        const response = await apiClient.get<IngestedDocument[]>('/api/v1/ingest/documents');
        return response.data;
    },
};

export const retrievalApi = {
    queryKnowledgeBase: async (request: QueryRequest): Promise<QueryResponse> => {
        const response = await apiClient.post<QueryResponse>('/api/v1/query/', request);
        return response.data;
    }
};