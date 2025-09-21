/**
 * API Service - Comunicação com Backend com Tratamento Global de Erros
 * Refatorado para usar Axios com interceptadores
 */

import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { toast } from '@/hooks/use-toast';

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
  private client: AxiosInstance;

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor - adiciona token de autenticação
    this.client.interceptors.request.use(
      (config) => {
        // Obter token do localStorage
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - tratamento global de erros
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error: AxiosError) => {
        return this.handleGlobalError(error);
      }
    );
  }

  private async handleGlobalError(error: AxiosError): Promise<never> {
    const status = error.response?.status || 0;
    const errorData = error.response?.data as any;
    
    switch (status) {
      case 401:
        // Token inválido ou expirado
        this.handleUnauthorized();
        break;
        
      case 403:
        toast({
          title: "Acesso Negado",
          description: "Você não tem permissão para realizar esta ação.",
          variant: "destructive",
        });
        break;
        
      case 404:
        toast({
          title: "Recurso Não Encontrado",
          description: "O recurso solicitado não foi encontrado.",
          variant: "destructive",
        });
        break;
        
      case 422:
        // Erro de validação
        const validationMessage = this.extractValidationMessage(errorData);
        toast({
          title: "Erro de Validação",
          description: validationMessage,
          variant: "destructive",
        });
        break;
        
      case 500:
        toast({
          title: "Erro Interno do Servidor",
          description: "Ocorreu um erro interno. Tente novamente mais tarde.",
          variant: "destructive",
        });
        break;
        
      case 0:
        // Network error
        toast({
          title: "Erro de Conexão",
          description: "Não foi possível conectar ao servidor. Verifique sua conexão.",
          variant: "destructive",
        });
        break;
        
      default:
        // Outros erros
        const message = errorData?.detail || errorData?.message || 'Erro desconhecido';
        toast({
          title: "Erro",
          description: message,
          variant: "destructive",
        });
    }

    // Criar erro padronizado
    const apiError: ApiError = {
      message: errorData?.detail || errorData?.message || `HTTP ${status}`,
      status,
      details: errorData,
    };

    return Promise.reject(apiError);
  }

  private handleUnauthorized(): void {
    // Limpar dados de autenticação
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_data');
    
    // Mostrar toast de sessão expirada
    toast({
      title: "Sessão Expirada",
      description: "Sua sessão expirou. Faça login novamente.",
      variant: "destructive",
    });
    
    // Redirecionar para login após um pequeno delay
    setTimeout(() => {
      window.location.href = '/login';
    }, 2000);
  }

  private extractValidationMessage(errorData: any): string {
    if (errorData?.detail) {
      if (Array.isArray(errorData.detail)) {
        return errorData.detail.map((err: any) => err.msg || err.message).join(', ');
      }
      return errorData.detail;
    }
    return 'Dados inválidos fornecidos.';
  }

  // Métodos HTTP públicos com suporte a AbortController
  async get<T>(endpoint: string, options?: { signal?: AbortSignal }): Promise<ApiResponse<T>> {
    const response = await this.client.get<T>(endpoint, {
      signal: options?.signal,
    });
    return {
      data: response.data,
      status: response.status,
    };
  }

  async post<T>(endpoint: string, data?: any, options?: { signal?: AbortSignal }): Promise<ApiResponse<T>> {
    const response = await this.client.post<T>(endpoint, data, {
      signal: options?.signal,
    });
    return {
      data: response.data,
      status: response.status,
    };
  }

  async put<T>(endpoint: string, data?: any, options?: { signal?: AbortSignal }): Promise<ApiResponse<T>> {
    const response = await this.client.put<T>(endpoint, data, {
      signal: options?.signal,
    });
    return {
      data: response.data,
      status: response.status,
    };
  }

  async delete<T>(endpoint: string, options?: { signal?: AbortSignal }): Promise<ApiResponse<T>> {
    const response = await this.client.delete<T>(endpoint, {
      signal: options?.signal,
    });
    return {
      data: response.data,
      status: response.status,
    };
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; app_name: string; version: string }>> {
    return this.get('/health');
  }

  // Método para atualizar token
  setAuthToken(token: string): void {
    localStorage.setItem('auth_token', token);
  }

  // Método para limpar token
  clearAuthToken(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_data');
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
