/**
 * Auth Store - Gerenciamento de Estado de Autenticação
 * Store Zustand para gerenciar estado de autenticação global
 */

import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

export interface AuthUser {
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

export interface AuthState {
  // Estado
  isAuthenticated: boolean;
  user: AuthUser | null;
  isLoading: boolean;
  error: string | null;
  
  // Computed values
  fullName: string;
  isSubscriptionActive: boolean;
  subscriptionDaysRemaining: number | null;
  
  // Actions
  actions: {
    setUser: (user: AuthUser) => void;
    setIsAuthenticated: (isAuthenticated: boolean) => void;
    setLoading: (isLoading: boolean) => void;
    setError: (error: string | null) => void;
    updateUser: (updates: Partial<AuthUser>) => void;
    logout: () => void;
    reset: () => void;
  };
}

const initialState = {
  isAuthenticated: false,
  user: null,
  isLoading: false,
  error: null,
};

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      subscribeWithSelector(
        immer((set, get) => ({
          // Estado inicial
          ...initialState,
          
          // Computed values
          get fullName() {
            const user = get().user;
            return user ? `${user.first_name} ${user.last_name}` : '';
          },
          
          get isSubscriptionActive() {
            const user = get().user;
            if (!user?.subscription_expires_at) return true; // Sem data de expiração = ativo
            
            const expirationDate = new Date(user.subscription_expires_at);
            return expirationDate > new Date();
          },
          
          get subscriptionDaysRemaining() {
            const user = get().user;
            if (!user?.subscription_expires_at) return null;
            
            const expirationDate = new Date(user.subscription_expires_at);
            const today = new Date();
            const diffTime = expirationDate.getTime() - today.getTime();
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            return diffDays > 0 ? diffDays : 0;
          },
          
          // Actions
          actions: {
            setUser: (user: AuthUser) => {
              set((state) => {
                state.user = user;
                state.error = null;
              });
            },
            
            setIsAuthenticated: (isAuthenticated: boolean) => {
              set((state) => {
                state.isAuthenticated = isAuthenticated;
                if (!isAuthenticated) {
                  state.user = null;
                }
              });
            },
            
            setLoading: (isLoading: boolean) => {
              set((state) => {
                state.isLoading = isLoading;
              });
            },
            
            setError: (error: string | null) => {
              set((state) => {
                state.error = error;
              });
            },
            
            updateUser: (updates: Partial<AuthUser>) => {
              set((state) => {
                if (state.user) {
                  Object.assign(state.user, updates);
                }
              });
            },
            
            logout: () => {
              set((state) => {
                state.isAuthenticated = false;
                state.user = null;
                state.error = null;
                state.isLoading = false;
              });
              
              // Limpar localStorage
              localStorage.removeItem('auth_token');
              localStorage.removeItem('refresh_token');
              localStorage.removeItem('user_data');
            },
            
            reset: () => {
              set((state) => {
                Object.assign(state, initialState);
              });
            },
          },
        }))
      ),
      {
        name: 'auth-store',
        partialize: (state) => ({
          isAuthenticated: state.isAuthenticated,
          user: state.user,
        }),
      }
    ),
    {
      name: 'auth-store',
    }
  )
);

// Selectors otimizados para evitar re-renders desnecessários
export const useAuthUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useAuthLoading = () => useAuthStore((state) => state.isLoading);
export const useAuthError = () => useAuthStore((state) => state.error);
export const useAuthActions = () => useAuthStore((state) => state.actions);

// Selectors computados
export const useUserFullName = () => useAuthStore((state) => state.fullName);
export const useSubscriptionStatus = () => useAuthStore((state) => ({
  isActive: state.isSubscriptionActive,
  daysRemaining: state.subscriptionDaysRemaining,
}));

// Selector para dados específicos do usuário
export const useUserProfile = () => useAuthStore((state) => {
  if (!state.user) return null;
  
  return {
    id: state.user.id,
    email: state.user.email,
    firstName: state.user.first_name,
    lastName: state.user.last_name,
    fullName: state.fullName,
    company: state.user.company,
    phone: state.user.phone,
    status: state.user.status,
    subscriptionType: state.user.subscription_type,
    subscriptionExpiresAt: state.user.subscription_expires_at,
    lastLogin: state.user.last_login,
    loginCount: state.user.login_count,
  };
});

// Hook para verificar permissões baseadas no tipo de assinatura
export const useUserPermissions = () => useAuthStore((state) => {
  const subscriptionType = state.user?.subscription_type;
  
  return {
    canCreateAgents: subscriptionType !== 'free',
    canCreateCampaigns: ['pro', 'enterprise'].includes(subscriptionType || ''),
    canAccessAnalytics: ['pro', 'enterprise'].includes(subscriptionType || ''),
    canManageTeam: subscriptionType === 'enterprise',
    maxAgents: subscriptionType === 'free' ? 1 : subscriptionType === 'basic' ? 5 : subscriptionType === 'pro' ? 20 : 100,
    maxCampaigns: subscriptionType === 'free' ? 0 : subscriptionType === 'basic' ? 2 : subscriptionType === 'pro' ? 10 : 50,
  };
};
