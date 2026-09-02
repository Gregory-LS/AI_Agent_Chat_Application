import type { Model } from '../types';

/**
 * Load available models from the backend API.
 *
 * The endpoint is expected to return a JSON array of objects with the shape:
 * [{ id: string, name: string, description?: string }]
 */
export async function fetchModels(): Promise<Model[]> {
  const response = await fetch('/api/models');

  if (!response.ok) {
    throw new Error(`Failed to load models: ${response.status} ${response.statusText}`);
  }

  return response.json();
}
