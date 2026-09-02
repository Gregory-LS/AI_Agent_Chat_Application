import { useCallback, useEffect, useState } from 'react';
import { fetchModels } from '../api/modelsApi';
import type { Model } from '../types';

export interface UseModelsOptions {
  fetchModels?: () => Promise<Model[]>;
  enabled?: boolean;
}

export function useModels({ fetchModels: fetchModelsImpl, enabled = true }: UseModelsOptions = {}) {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState<boolean>(enabled);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!enabled) {
      setModels([]);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const fetcher = fetchModelsImpl ?? fetchModels;
      const data = await fetcher();
      setModels(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load models.');
      setModels([]);
    } finally {
      setLoading(false);
    }
  }, [fetchModelsImpl, enabled]);

  useEffect(() => {
    load();
  }, [load]);

  const retry = useCallback(() => load(), [load]);

  return { models, loading, error, retry };
}
