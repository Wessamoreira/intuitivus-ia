/**
 * Testes unitários para o serviço de API
 * Equivalente aos testes JUnit em Java
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { apiService, ApiError } from '../api';

// Mock do fetch global
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('ApiService', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('GET requests', () => {
    it('should make successful GET request', async () => {
      const mockData = { message: 'success' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockData,
      });

      const result = await apiService.get('/test');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(result).toEqual({
        data: mockData,
        status: 200,
      });
    });

    it('should handle GET request errors', async () => {
      const errorData = { detail: 'Not found' };
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => errorData,
      });

      await expect(apiService.get('/not-found')).rejects.toEqual({
        message: 'Not found',
        status: 404,
        details: errorData,
      });
    });
  });

  describe('POST requests', () => {
    it('should make successful POST request with data', async () => {
      const requestData = { name: 'Test User' };
      const responseData = { id: 1, name: 'Test User' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => responseData,
      });

      const result = await apiService.post('/users', requestData);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/users',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(requestData),
        })
      );

      expect(result).toEqual({
        data: responseData,
        status: 201,
      });
    });

    it('should make POST request without data', async () => {
      const responseData = { message: 'created' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => responseData,
      });

      const result = await apiService.post('/action');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/action',
        expect.objectContaining({
          method: 'POST',
          body: undefined,
        })
      );

      expect(result.data).toEqual(responseData);
    });
  });

  describe('PUT requests', () => {
    it('should make successful PUT request', async () => {
      const requestData = { name: 'Updated User' };
      const responseData = { id: 1, name: 'Updated User' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => responseData,
      });

      const result = await apiService.put('/users/1', requestData);

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/users/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(requestData),
        })
      );

      expect(result.data).toEqual(responseData);
    });
  });

  describe('DELETE requests', () => {
    it('should make successful DELETE request', async () => {
      const responseData = { message: 'deleted' };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => responseData,
      });

      const result = await apiService.delete('/users/1');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/users/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      );

      expect(result.data).toEqual(responseData);
    });
  });

  describe('Health check', () => {
    it('should perform health check successfully', async () => {
      const healthData = {
        status: 'healthy',
        app_name: 'Intuitivus Flow Studio',
        version: '1.0.0',
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => healthData,
      });

      const result = await apiService.healthCheck();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/health',
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(result.data).toEqual(healthData);
    });
  });

  describe('Error handling', () => {
    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new TypeError('Network error'));

      await expect(apiService.get('/test')).rejects.toEqual({
        message: 'Erro de conexão com o servidor',
        status: 0,
        details: expect.any(TypeError),
      });
    });

    it('should handle HTTP errors without JSON response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      await expect(apiService.get('/test')).rejects.toEqual({
        message: 'HTTP 500',
        status: 500,
        details: {},
      });
    });

    it('should handle custom error messages', async () => {
      const errorData = { detail: 'Custom error message' };
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => errorData,
      });

      await expect(apiService.get('/test')).rejects.toEqual({
        message: 'Custom error message',
        status: 400,
        details: errorData,
      });
    });
  });

  describe('Configuration', () => {
    it('should use custom base URL', async () => {
      const customApiService = new (apiService.constructor as any)('https://api.example.com');
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
      });

      await customApiService.get('/test');

      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/test',
        expect.any(Object)
      );
    });

    it('should include custom headers', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
      });

      await apiService.get('/test');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });
  });
});
