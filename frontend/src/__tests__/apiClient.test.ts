import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api, setAuthToken, getAuthToken } from '../api/client';

describe('Typed API Client', () => {
  beforeEach(() => {
    setAuthToken(null);
    vi.restoreAllMocks();
  });

  it('manages token in memory and injects Authorization header into requests', async () => {
    setAuthToken('synthetic-test-token-value-12345');
    expect(getAuthToken()).toBe('synthetic-test-token-value-12345');

    const mockResponse = {
      dataset_name: 'test-dataset',
      total_log_lines: 10,
      precision: 1.0,
      recall: 1.0,
      f1_score: 1.0,
      services_detected: 4,
      expected_services: 4,
      edges_detected: 3,
      expected_edges: 3,
      failure_patterns_detected: 1,
      evaluated_at: new Date().toISOString(),
      notes: 'test'
    };

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    } as Response);

    const result = await api.getBenchmark();
    expect(result.f1_score).toBe(1.0);
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    const callArgs = fetchSpy.mock.calls[0];
    const headers = callArgs[1]?.headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer synthetic-test-token-value-12345');
  });

  it('handles backend error details appropriately', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Log content cannot be empty.' })
    } as Response);

    await expect(api.analyzeLogs('')).rejects.toThrow('Log content cannot be empty.');
  });
});
