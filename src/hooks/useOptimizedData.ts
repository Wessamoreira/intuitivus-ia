/**
 * Optimized Data Hooks
 * Hooks otimizados que combinam React Query com Zustand
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import { apiService } from '@/services/api';
import { useAppActions, useAppStore } from '@/stores/useAppStore';
import { toast } from '@/hooks/use-toast';
import type { Agent, Task, Campaign } from '@/stores/types';

// Query keys para cache
export const QUERY_KEYS = {
  agents: ['agents'] as const,
  agent: (id: string) => ['agents', id] as const,
  tasks: ['tasks'] as const,
  task: (id: string) => ['tasks', id] as const,
  campaigns: ['campaigns'] as const,
  campaign: (id: string) => ['campaigns', id] as const,
  dashboardStats: ['dashboard', 'stats'] as const,
  userProfile: ['user', 'profile'] as const,
} as const;

// Hook para agentes otimizado
export const useOptimizedAgents = () => {
  const { setAgents, setLoading, setError } = useAppActions();
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: QUERY_KEYS.agents,
    queryFn: async () => {
      const response = await apiService.get<Agent[]>('/api/v1/agents');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutos
    gcTime: 10 * 60 * 1000, // 10 minutos
    refetchOnWindowFocus: false,
    onSuccess: (data) => {
      setAgents(data);
      setLoading('agents', false);
      setError('agents', null);
    },
    onError: (error: any) => {
      setError('agents', error.message);
      setLoading('agents', false);
      toast({
        title: "Erro ao carregar agentes",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Mutation para criar agente
  const createAgentMutation = useMutation({
    mutationFn: async (agentData: Partial<Agent>) => {
      const response = await apiService.post<Agent>('/api/v1/agents', agentData);
      return response.data;
    },
    onSuccess: (newAgent) => {
      // Invalidar cache e atualizar store
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.agents });
      
      // Otimistic update
      queryClient.setQueryData<Agent[]>(QUERY_KEYS.agents, (old) => {
        return old ? [...old, newAgent] : [newAgent];
      });

      toast({
        title: "Agente criado",
        description: `${newAgent.name} foi criado com sucesso.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Erro ao criar agente",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Mutation para atualizar status do agente
  const updateAgentStatusMutation = useMutation({
    mutationFn: async ({ agentId, status }: { agentId: string; status: string }) => {
      const response = await apiService.put<Agent>(`/api/v1/agents/${agentId}/status`, { status });
      return response.data;
    },
    onMutate: async ({ agentId, status }) => {
      // Cancelar queries em andamento
      await queryClient.cancelQueries({ queryKey: QUERY_KEYS.agents });

      // Snapshot do estado anterior
      const previousAgents = queryClient.getQueryData<Agent[]>(QUERY_KEYS.agents);

      // Optimistic update
      queryClient.setQueryData<Agent[]>(QUERY_KEYS.agents, (old) => {
        return old?.map(agent => 
          agent.id === agentId ? { ...agent, status } : agent
        ) || [];
      });

      return { previousAgents };
    },
    onError: (error: any, variables, context) => {
      // Reverter optimistic update
      if (context?.previousAgents) {
        queryClient.setQueryData(QUERY_KEYS.agents, context.previousAgents);
      }
      
      toast({
        title: "Erro ao atualizar agente",
        description: error.message,
        variant: "destructive",
      });
    },
    onSettled: () => {
      // Sempre refetch após mutation
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.agents });
    },
  });

  return {
    agents: query.data || [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
    createAgent: createAgentMutation.mutate,
    updateAgentStatus: updateAgentStatusMutation.mutate,
    isCreating: createAgentMutation.isPending,
    isUpdatingStatus: updateAgentStatusMutation.isPending,
  };
};

// Hook para tarefas otimizado
export const useOptimizedTasks = (filters?: { status?: string; agentId?: string }) => {
  const { setTasks, setLoading, setError } = useAppActions();
  const queryClient = useQueryClient();

  // Criar query key dinâmica baseada nos filtros
  const queryKey = useMemo(() => {
    return filters ? [...QUERY_KEYS.tasks, filters] : QUERY_KEYS.tasks;
  }, [filters]);

  const query = useQuery({
    queryKey,
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.agentId) params.append('agent_id', filters.agentId);
      
      const response = await apiService.get<Task[]>(`/api/v1/tasks?${params.toString()}`);
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutos (tarefas mudam mais frequentemente)
    gcTime: 5 * 60 * 1000,
    refetchInterval: 30 * 1000, // Refetch a cada 30 segundos para tarefas ativas
    refetchIntervalInBackground: false,
    onSuccess: (data) => {
      if (!filters) {
        setTasks(data);
      }
      setLoading('tasks', false);
      setError('tasks', null);
    },
    onError: (error: any) => {
      setError('tasks', error.message);
      setLoading('tasks', false);
    },
  });

  // Mutation para atualizar status da tarefa
  const updateTaskStatusMutation = useMutation({
    mutationFn: async ({ taskId, status }: { taskId: string; status: string }) => {
      const response = await apiService.put<Task>(`/api/v1/tasks/${taskId}/status`, { status });
      return response.data;
    },
    onMutate: async ({ taskId, status }) => {
      await queryClient.cancelQueries({ queryKey: QUERY_KEYS.tasks });

      const previousTasks = queryClient.getQueryData<Task[]>(QUERY_KEYS.tasks);

      // Optimistic update para todas as queries de tasks
      queryClient.setQueriesData<Task[]>(
        { queryKey: ['tasks'] },
        (old) => {
          return old?.map(task => 
            task.id === taskId ? { ...task, status } : task
          ) || [];
        }
      );

      return { previousTasks };
    },
    onError: (error: any, variables, context) => {
      if (context?.previousTasks) {
        queryClient.setQueryData(QUERY_KEYS.tasks, context.previousTasks);
      }
      
      toast({
        title: "Erro ao atualizar tarefa",
        description: error.message,
        variant: "destructive",
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  return {
    tasks: query.data || [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
    updateTaskStatus: updateTaskStatusMutation.mutate,
    isUpdatingStatus: updateTaskStatusMutation.isPending,
  };
};

// Hook para estatísticas do dashboard
export const useOptimizedDashboardStats = () => {
  const query = useQuery({
    queryKey: QUERY_KEYS.dashboardStats,
    queryFn: async () => {
      const response = await apiService.get('/api/v1/dashboard/stats');
      return response.data;
    },
    staleTime: 1 * 60 * 1000, // 1 minuto
    gcTime: 5 * 60 * 1000,
    refetchInterval: 60 * 1000, // Refetch a cada minuto
    refetchOnWindowFocus: true,
    retry: (failureCount, error: any) => {
      // Não tentar novamente para erros 4xx
      if (error?.status >= 400 && error?.status < 500) {
        return false;
      }
      return failureCount < 3;
    },
  });

  // Dados computados memoizados
  const computedStats = useMemo(() => {
    if (!query.data) return null;

    const data = query.data;
    return {
      ...data,
      completionRate: data.totalTasks > 0 ? Math.round((data.completedTasks / data.totalTasks) * 100) : 0,
      activeAgentsPercentage: data.totalAgents > 0 ? Math.round((data.activeAgents / data.totalAgents) * 100) : 0,
      growthTrend: data.monthlyGrowth > 0 ? 'up' : data.monthlyGrowth < 0 ? 'down' : 'stable',
    };
  }, [query.data]);

  return {
    stats: computedStats,
    rawData: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
};

// Hook para invalidar caches relacionados
export const useCacheInvalidation = () => {
  const queryClient = useQueryClient();

  const invalidateAgents = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.agents });
  }, [queryClient]);

  const invalidateTasks = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['tasks'] });
  }, [queryClient]);

  const invalidateDashboard = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboardStats });
  }, [queryClient]);

  const invalidateAll = useCallback(() => {
    queryClient.invalidateQueries();
  }, [queryClient]);

  const clearCache = useCallback(() => {
    queryClient.clear();
  }, [queryClient]);

  return {
    invalidateAgents,
    invalidateTasks,
    invalidateDashboard,
    invalidateAll,
    clearCache,
  };
};

// Hook para prefetch de dados
export const useDataPrefetch = () => {
  const queryClient = useQueryClient();

  const prefetchAgents = useCallback(() => {
    queryClient.prefetchQuery({
      queryKey: QUERY_KEYS.agents,
      queryFn: async () => {
        const response = await apiService.get<Agent[]>('/api/v1/agents');
        return response.data;
      },
      staleTime: 5 * 60 * 1000,
    });
  }, [queryClient]);

  const prefetchTasks = useCallback(() => {
    queryClient.prefetchQuery({
      queryKey: QUERY_KEYS.tasks,
      queryFn: async () => {
        const response = await apiService.get<Task[]>('/api/v1/tasks');
        return response.data;
      },
      staleTime: 2 * 60 * 1000,
    });
  }, [queryClient]);

  const prefetchDashboard = useCallback(() => {
    queryClient.prefetchQuery({
      queryKey: QUERY_KEYS.dashboardStats,
      queryFn: async () => {
        const response = await apiService.get('/api/v1/dashboard/stats');
        return response.data;
      },
      staleTime: 1 * 60 * 1000,
    });
  }, [queryClient]);

  return {
    prefetchAgents,
    prefetchTasks,
    prefetchDashboard,
  };
};
