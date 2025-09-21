import React, { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from '@/components/ui/toaster';
import { useAppStore } from '@/stores/useAppStore';

// Configuração otimizada do React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutos
      cacheTime: 10 * 60 * 1000, // 10 minutos
      retry: (failureCount, error: any) => {
        // Não retry em erros 4xx
        if (error?.status >= 400 && error?.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

interface AppProviderProps {
  children: React.ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const { actions } = useAppStore();

  // Inicializar dados da aplicação
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Verificar se há token de autenticação
        const token = localStorage.getItem('auth_token');
        if (token) {
          // Carregar dados do usuário
          // TODO: Implementar carregamento real do usuário
          actions.setUser({
            id: '1',
            email: 'user@example.com',
            firstName: 'John',
            lastName: 'Doe',
            status: 'active',
            subscriptionType: 'pro',
            loginCount: 42,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          });

          // Carregar dados iniciais (mock)
          actions.setAgents([
            {
              id: '1',
              name: 'Marketing Specialist',
              type: 'Marketing',
              status: 'active',
              description: 'AI agent specialized in marketing campaigns',
              configuration: {},
              tasksCompleted: 45,
              successRate: 94,
              lastActivity: '2 min ago',
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              userId: '1',
            },
            {
              id: '2',
              name: 'Customer Support Bot',
              type: 'Support',
              status: 'active',
              description: 'AI agent for customer support',
              configuration: {},
              tasksCompleted: 128,
              successRate: 98,
              lastActivity: '5 min ago',
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              userId: '1',
            },
            {
              id: '3',
              name: 'Content Creator AI',
              type: 'Content',
              status: 'paused',
              description: 'AI agent for content creation',
              configuration: {},
              tasksCompleted: 23,
              successRate: 87,
              lastActivity: '1 hour ago',
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              userId: '1',
            },
          ]);

          actions.setTasks([
            {
              id: '1',
              agentId: '1',
              type: 'Campaign Analysis',
              status: 'completed',
              input: { campaign_id: 'camp_123' },
              output: { analysis: 'Campaign performing well' },
              executionTime: 1250,
              createdAt: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
              updatedAt: new Date().toISOString(),
            },
            {
              id: '2',
              agentId: '2',
              type: 'Customer Query',
              status: 'running',
              input: { query: 'How to reset password?' },
              createdAt: new Date(Date.now() - 30 * 1000).toISOString(),
              updatedAt: new Date().toISOString(),
            },
            {
              id: '3',
              agentId: '1',
              type: 'Ad Optimization',
              status: 'failed',
              input: { ad_id: 'ad_456' },
              error: 'API rate limit exceeded',
              createdAt: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
              updatedAt: new Date().toISOString(),
            },
          ]);

          actions.setCampaigns([
            {
              id: '1',
              name: 'Summer Sale Campaign',
              platform: 'google_ads',
              status: 'active',
              budget: 5000,
              spent: 3200,
              impressions: 125000,
              clicks: 2500,
              conversions: 125,
              startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              userId: '1',
            },
            {
              id: '2',
              name: 'Brand Awareness',
              platform: 'meta_ads',
              status: 'active',
              budget: 3000,
              spent: 1800,
              impressions: 89000,
              clicks: 1200,
              conversions: 45,
              startDate: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              userId: '1',
            },
          ]);
        }
      } catch (error) {
        console.error('Failed to initialize app:', error);
        actions.setError('global', 'Failed to initialize application');
      }
    };

    initializeApp();
  }, [actions]);

  // Cleanup de notificações expiradas
  useEffect(() => {
    const interval = setInterval(() => {
      const { notifications, actions } = useAppStore.getState();
      const now = new Date();
      
      notifications.forEach((notification) => {
        if (notification.expiresAt && new Date(notification.expiresAt) < now) {
          actions.removeNotification(notification.id);
        }
      });
    }, 60000); // Check a cada minuto

    return () => clearInterval(interval);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Toaster />
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};
