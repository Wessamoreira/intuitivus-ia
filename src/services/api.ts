/**
 * API Service - Comunicação com Backend
 * Equivalente aos serviços REST em Java/Spring
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
}

class ApiService {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw {
          message: errorData.detail || `HTTP ${response.status}`,
          status: response.status,
          details: errorData,
        } as ApiError;
      }

      const data = await response.json();
      
      return {
        data,
        status: response.status,
      };
    } catch (error) {
      if (error instanceof TypeError) {
        // Network error
        throw {
          message: 'Erro de conexão com o servidor',
          status: 0,
          details: error,
        } as ApiError;
      }
      throw error;
    }
  }

  // GET request
  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  // POST request
  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // PUT request
  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // DELETE request
  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; app_name: string; version: string }>> {
    return this.get('/health');
  }
}

// Instância singleton
export const apiService = new ApiService();

// Hooks específicos para diferentes recursos
export const useApi = () => {
  return {
    // Health check
    healthCheck: () => apiService.healthCheck(),
    
    // Users
    getUsers: () => apiService.get('/api/v1/users'),
    createUser: (userData: any) => apiService.post('/api/v1/users', userData),
    
    // Agents
    getAgents: () => apiService.get('/api/v1/agents'),
    createAgent: (agentData: any) => apiService.post('/api/v1/agents', agentData),
    
    // Tasks
    getTasks: () => apiService.get('/api/v1/tasks'),
    createTask: (taskData: any) => apiService.post('/api/v1/tasks', taskData),
    
    // Campaigns
    getCampaigns: () => apiService.get('/api/v1/campaigns'),
    createCampaign: (campaignData: any) => apiService.post('/api/v1/campaigns', campaignData),
  };
};

export default apiService;
