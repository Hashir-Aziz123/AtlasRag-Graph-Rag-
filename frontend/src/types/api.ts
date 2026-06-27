export type TaskStatus = 'PENDING' | 'STARTED' | 'SUCCESS' | 'FAILURE';

export interface UploadResponse {
    message: string;
    task_id: string;
}

export interface TaskStatusResponse {
    task_id: string;
    status: TaskStatus;
    result?: string;
}

export interface QueryRequest {
    query: string;
}

export interface QueryResponse {
    answer: string;
    routed_intent: string;
}

export interface IngestedDocument {
    id: string;
    filename: string;
    chunk_count: number;
    created_at: string | null;
}