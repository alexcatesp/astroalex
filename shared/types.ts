/**
 * Shared TypeScript types between frontend and backend
 * These types should match the Pydantic models in the backend
 */

export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  path: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface FileMetadata {
  filename: string;
  image_type: 'Light' | 'Dark' | 'Bias' | 'Flat';
  object_name?: string;
  filter?: string;
  exposure_time?: number;
  gain?: number;
  date?: string;
  sequence?: string;
}

export interface CalibrationSession {
  id: string;
  name: string;
  date: string;
  telescope?: string;
  camera?: string;
}

export interface MasterCalibration {
  id: string;
  session_id: string;
  type: 'Bias' | 'Dark' | 'Flat';
  exposure_time?: number;
  gain?: number;
  filename: string;
  created_at: string;
}

export interface ProcessingPipeline {
  id: string;
  project_id: string;
  object_name: string;
  filters: string[];
  steps: ProcessingStep[];
  status: 'pending' | 'running' | 'completed' | 'failed';
}

export interface ProcessingStep {
  type: 'calibration' | 'quality_analysis' | 'registration' | 'stacking';
  config: Record<string, unknown>;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}
