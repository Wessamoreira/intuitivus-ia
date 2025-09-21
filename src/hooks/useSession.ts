/**
 * Hook de Sessão - Gerencia autenticação e validação de token
 * Verifica se o usuário está autenticado ao iniciar a aplicação
 */

import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';
import { useAuthStore } from '@/stores/useAuthStore';
import { toast } from '@/hooks/use-toast';

export interface SessionUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  company?: string;
  phone?: string;
  status: string;
  subscription_type: string;
  subscription_expires_at?: string;
  created_at: string;
  last_login?: string;
  login_count: number;
}

export interface SessionState {
  isLoading: boolean;
  isAuthenticated: boolean;
  user: SessionUser | null;
  error: string | null;
}

export const useSession = () => {
  const [sessionState, setSessionState] = useState<SessionState>({
    isLoading: true,
    isAuthenticated: false,
    user: null,
    error: null,
  });

  const { setUser, setIsAuthenticated, logout } = useAuthStore((state) => ({
    setUser: state.actions.setUser,
    setIsAuthenticated: state.actions.setIsAuthenticated,
    logout: state.actions.logout,
  }));

  const validateSession = async () => {
    try {
      setSessionState(prev => ({ ...prev, isLoading: true, error: null }));

      // Verificar se existe token no localStorage
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('No token found');
      }

      // Fazer chamada para validar o token e obter dados do usuário
      const response = await apiService.get<SessionUser>('/api/v1/auth/me');
      const userData = response.data;

      // Atualizar estado da sessão
      setSessionState({
        isLoading: false,
        isAuthenticated: true,
        user: userData,
        error: null,
      });

      // Atualizar store de autenticação
      setUser(userData);
      setIsAuthenticated(true);

      // Salvar dados do usuário no localStorage
      localStorage.setItem('user_data', JSON.stringify(userData));

    } catch (error: any) {
      // Token inválido ou erro na validação
      console.warn('Session validation failed:', error);

      // Limpar dados de autenticação
      logout();
      apiService.clearAuthToken();

      // Atualizar estado da sessão
      setSessionState({
        isLoading: false,
        isAuthenticated: false,
        user: null,
        error: error.message || 'Session validation failed',
      });
    }
  };

  const refreshSession = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token found');
      }

      const response = await apiService.post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
      }>('/api/v1/auth/refresh', {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token: newRefreshToken } = response.data;

      // Atualizar tokens
      localStorage.setItem('auth_token', access_token);
      localStorage.setItem('refresh_token', newRefreshToken);
      apiService.setAuthToken(access_token);

      // Revalidar sessão com novo token
      await validateSession();

      toast({
        title: "Sessão Renovada",
        description: "Sua sessão foi renovada automaticamente.",
      });

    } catch (error: any) {
      console.error('Token refresh failed:', error);
      
      // Se refresh falhar, fazer logout
      logout();
      apiService.clearAuthToken();
      
      setSessionState({
        isLoading: false,
        isAuthenticated: false,
        user: null,
        error: 'Session expired',
      });

      toast({
        title: "Sessão Expirada",
        description: "Sua sessão expirou. Faça login novamente.",
        variant: "destructive",
      });
    }
  };

  const initializeSession = async () => {
    try {
      // Tentar validar sessão atual
      await validateSession();
    } catch (error: any) {
      // Se validação falhar, tentar refresh
      if (error.status === 401) {
        await refreshSession();
      } else {
        // Outros erros, fazer logout
        logout();
        apiService.clearAuthToken();
        
        setSessionState({
          isLoading: false,
          isAuthenticated: false,
          user: null,
          error: error.message,
        });
      }
    }
  };

  const login = async (email: string, password: string) => {
    try {
      setSessionState(prev => ({ ...prev, isLoading: true, error: null }));

      const response = await apiService.post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
        id: string;
        email: string;
        first_name: string;
        last_name: string;
        company?: string;
        phone?: string;
        status: string;
        subscription_type: string;
        subscription_expires_at?: string;
        last_login?: string;
        login_count: number;
      }>('/api/v1/auth/login', {
        email,
        password,
      });

      const { access_token, refresh_token, ...userData } = response.data;

      // Salvar tokens
      localStorage.setItem('auth_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user_data', JSON.stringify(userData));
      apiService.setAuthToken(access_token);

      // Atualizar estado
      setSessionState({
        isLoading: false,
        isAuthenticated: true,
        user: userData as SessionUser,
        error: null,
      });

      // Atualizar store
      setUser(userData as SessionUser);
      setIsAuthenticated(true);

      toast({
        title: "Login Realizado",
        description: `Bem-vindo, ${userData.first_name}!`,
      });

      return { success: true, user: userData };

    } catch (error: any) {
      setSessionState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message,
      }));

      return { success: false, error: error.message };
    }
  };

  const logoutSession = () => {
    // Limpar estado local
    setSessionState({
      isLoading: false,
      isAuthenticated: false,
      user: null,
      error: null,
    });

    // Limpar store
    logout();
    apiService.clearAuthToken();

    toast({
      title: "Logout Realizado",
      description: "Você foi desconectado com sucesso.",
    });
  };

  // Inicializar sessão ao montar o hook
  useEffect(() => {
    initializeSession();
  }, []);

  // Auto-refresh token a cada 25 minutos (tokens expiram em 30 min)
  useEffect(() => {
    if (sessionState.isAuthenticated) {
      const refreshInterval = setInterval(() => {
        refreshSession();
      }, 25 * 60 * 1000); // 25 minutos

      return () => clearInterval(refreshInterval);
    }
  }, [sessionState.isAuthenticated]);

  return {
    ...sessionState,
    login,
    logout: logoutSession,
    refreshSession,
    validateSession,
  };
};
