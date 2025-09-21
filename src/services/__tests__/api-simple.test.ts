/**
 * Teste simples da API - Verificação rápida
 */

import { describe, it, expect, vi } from 'vitest';

describe('API Simple Test', () => {
  it('should pass basic test', () => {
    expect(1 + 1).toBe(2);
  });

  it('should mock fetch successfully', () => {
    const mockFetch = vi.fn();
    global.fetch = mockFetch;
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ status: 'healthy' }),
    });

    expect(mockFetch).toBeDefined();
  });

  it('should test API service import', async () => {
    // Teste básico de importação
    const { apiService } = await import('../api');
    expect(apiService).toBeDefined();
  });
});
