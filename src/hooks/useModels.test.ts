import { act, renderHook, waitFor } from '@testing-library/react';
import { useModels } from './useModels';
import type { Model } from '../types';

const models: Model[] = [
  { id: 'a', name: 'Model A' },
  { id: 'b', name: 'Model B' },
];

describe('useModels', () => {
  it('loads models successfully', async () => {
    const fetchModels = jest.fn().mockResolvedValue(models);

    const { result } = renderHook(() => useModels({ fetchModels }));

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.models).toEqual(models);
    expect(result.current.error).toBeNull();
    expect(fetchModels).toHaveBeenCalledTimes(1);
  });

  it('stores an error message when the request fails', async () => {
    const fetchModels = jest.fn().mockRejectedValue(new Error('Network down'));

    const { result } = renderHook(() => useModels({ fetchModels }));

    await waitFor(() => expect(result.current.error).toBe('Network down'));
    expect(result.current.models).toEqual([]);
    expect(result.current.loading).toBe(false);
  });

  it('does not fetch when disabled', () => {
    const fetchModels = jest.fn();

    const { result } = renderHook(() => useModels({ fetchModels, enabled: false }));

    expect(fetchModels).not.toHaveBeenCalled();
    expect(result.current.models).toEqual([]);
    expect(result.current.loading).toBe(false);
  });

  it('can retry after a failure', async () => {
    const fetchModels = jest
      .fn()
      .mockRejectedValueOnce(new Error('First failure'))
      .mockResolvedValueOnce(models);

    const { result } = renderHook(() => useModels({ fetchModels }));

    await waitFor(() => expect(result.current.error).toBe('First failure'));

    await act(async () => {
      result.current.retry();
    });

    await waitFor(() => expect(result.current.models).toEqual(models));
    expect(fetchModels).toHaveBeenCalledTimes(2);
  });
});
