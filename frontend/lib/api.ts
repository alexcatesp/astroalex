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

  // ========== V2.0 Equipment & Config APIs ==========

  // Equipment Profiles
  async getEquipmentProfiles() {
    return this.get<any[]>('/equipment/profiles/');
  }

  async getActiveEquipmentProfile() {
    return this.get<any>('/equipment/profiles/active');
  }

  async getEquipmentProfile(id: string) {
    return this.get<any>(`/equipment/profiles/${id}`);
  }

  async createEquipmentProfile(data: any) {
    return this.post<any>('/equipment/profiles/', data);
  }

  async updateEquipmentProfile(id: string, data: any) {
    return this.put<any>(`/equipment/profiles/${id}`, data);
  }

  async deleteEquipmentProfile(id: string) {
    return this.delete<void>(`/equipment/profiles/${id}`);
  }

  async activateEquipmentProfile(id: string) {
    return this.post<any>(`/equipment/profiles/${id}/activate`, {});
  }

  // Configuration & User State
  async getAppConfig() {
    return this.get<any>('/config/');
  }

  async getUserState() {
    return this.get<any>('/config/user-state');
  }

  async updateUserState(updates: any) {
    return this.post<any>('/config/user-state', updates);
  }

  async getStorageConfig() {
    return this.get<any>('/config/storage');
  }

  async setStorageConfig(config: any) {
    return this.put<any>('/config/storage', config);
  }

  async completeOnboarding() {
    return this.post<any>('/config/onboarding/complete', {});
  }

  // Sessions (V2.0)
  async getSessions() {
    return this.get<any[]>('/sessions/');
  }

  async getSession(id: string) {
    return this.get<any>(`/sessions/${id}`);
  }

  async createSession(data: any) {
    return this.post<any>('/sessions/', data);
  }

  async updateSession(id: string, data: any) {
    return this.post<any>(`/sessions/${id}`, data);
  }

  async deleteSession(id: string) {
    return this.delete<void>(`/sessions/${id}`);
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
