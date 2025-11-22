/**
 * API client for communicating with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // Health check
  async healthCheck() {
    return this.get<{ status: string; dependencies: Record<string, string> }>('/health');
  }

  // Root status
  async getStatus() {
    return this.get<{ status: string; service: string; version: string }>('/');
  }

  // Projects
  async getProjects() {
    return this.get<any[]>('/projects');
  }

  async getProject(id: string) {
    return this.get<any>(`/projects/${id}`);
  }

  async createProject(data: { name: string; description?: string }) {
    return this.post<any>('/projects', data);
  }

  async updateProject(id: string, data: { name?: string; description?: string }) {
    return this.put<any>(`/projects/${id}`, data);
  }

  async deleteProject(id: string, deleteFiles: boolean = false) {
    return this.delete<void>(`/projects/${id}?delete_files=${deleteFiles}`);
  }

  async validateProject(id: string) {
    return this.get<{ project_id: string; valid: boolean; message: string }>(
      `/projects/${id}/validate`
    );
  }

  // Ingestion
  async scanIngestDirectory(projectId: string) {
    return this.get<any[]>(`/projects/${projectId}/ingest/scan`);
  }

  async getIngestStats(projectId: string) {
    return this.get<any>(`/projects/${projectId}/ingest/stats`);
  }

  async organizeFiles(
    projectId: string,
    sessionName?: string,
    copy: boolean = false
  ) {
    const params = new URLSearchParams();
    if (sessionName) params.append('session_name', sessionName);
    params.append('copy', String(copy));

    return this.post<any>(
      `/projects/${projectId}/ingest/organize?${params.toString()}`
    );
  }

  // Calibration - Sessions
  async createCalibrationSession(
    projectId: string,
    data: { name: string; date: string; telescope?: string; camera?: string }
  ) {
    return this.post<any>(`/projects/${projectId}/calibration/sessions`, data);
  }

  async getCalibrationSessions(projectId: string) {
    return this.get<any[]>(`/projects/${projectId}/calibration/sessions`);
  }

  async getCalibrationSession(projectId: string, sessionId: string) {
    return this.get<any>(`/projects/${projectId}/calibration/sessions/${sessionId}`);
  }

  // Calibration - Frame scanning
  async scanCalibrationFrames(
    projectId: string,
    sessionName: string,
    frameType: 'bias' | 'darks' | 'flats'
  ) {
    return this.get<any>(
      `/projects/${projectId}/calibration/sessions/${sessionName}/frames/${frameType}`
    );
  }

  // Calibration - Masters
  async createMaster(projectId: string, data: any) {
    return this.post<any>(`/projects/${projectId}/calibration/masters`, data);
  }

  async getMasters(projectId: string, sessionId?: string) {
    const params = sessionId ? `?session_id=${sessionId}` : '';
    return this.get<any[]>(`/projects/${projectId}/calibration/masters${params}`);
  }

  async getMaster(projectId: string, masterId: string) {
    return this.get<any>(`/projects/${projectId}/calibration/masters/${masterId}`);
  }

  async deleteMaster(projectId: string, masterId: string, deleteFile: boolean = false) {
    return this.delete<void>(
      `/projects/${projectId}/calibration/masters/${masterId}?delete_file=${deleteFile}`
    );
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
