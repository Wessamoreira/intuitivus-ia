/**
 * Agents Data Hooks
 * Hooks granulares para gerenciar dados de agentes usando React Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import { apiService } from '@/services/api';
import { useFilters } from '@/stores/useUIStore';
import { toast } from '@/hooks/use-toast';

export interface Agent {
  id: string;
  name: string;
  type: string;
  description?: string;
  status: 'active' | 'inactive' | 'error' | 'processing';
  avatar?: string;
  tasksCompleted?: number;
  tasksTotal?: number;
  lastActivity?: string;
  createdAt: string;
  updatedAt: string;
  config?: Record<string, any>;
  performance?: {
    successRate: number;
    averageResponseTime: number;
    totalTasks: number;
  };
}

export interface CreateAgentData {
  name: string;
  type: string;
  description?: string;
  config?: Record<string, any>;
}

export interface UpdateAgentData extends Partial<CreateAgentData> {
  status?: Agent['status'];
}

// Query keys
export const AGENTS_QUERY_KEYS = {
  all: ['agents'] as const,
  lists: () => [...AGENTS_QUERY_KEYS.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...AGENTS_QUERY_KEYS.lists(), filters] as const,
  details: () => [...AGENTS_QUERY_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...AGENTS_QUERY_KEYS.details(), id] as const,
  performance: (id: string) => [...AGENTS_QUERY_KEYS.detail(id), 'performance'] as const,
};

// Hook principal para listar agentes
export const useAgents = (options?: {
  status?: string;
  type?: string;
  enabled?: boolean;
}) => {
  const filters = useFilters();
  
  // Combinar filtros da UI com opções do hook
  const queryFilters = useMemo(() => ({
    status: options?.status || filters.agents.status || undefined,
    type: options?.type || filters.agents.type || undefined,
    sortBy: filters.agents.sortBy,
    sortOrder: filters.agents.sortOrder,
    search: filters.agents.searchTerm || undefined,
  }), [options, filters.agents]);

  const query = useQuery({
    queryKey: AGENTS_QUERY_KEYS.list(queryFilters),
    queryFn: async () => {
      const params = new URLSearchParams();
      
      Object.entries(queryFilters).forEach(([key, value]) => {
        if (value) params.append(key, value.toString());
      });
      
      const response = await apiService.get<Agent[]>(`/api/v1/agents?${params.toString()}`);
      return response.data;
    },
    enabled: options?.enabled !== false,
    staleTime: 5 * 60 * 1000, // 5 minutos
    gcTime: 10 * 60 * 1000, // 10 minutos
    refetchOnWindowFocus: false,
  });

  // Dados computados
  const computedData = useMemo(() => {
    if (!query.data) return null;

    const agents = query.data;
    return {
      total: agents.length,
      active: agents.filter(a => a.status === 'active').length,
      inactive: agents.filter(a => a.status === 'inactive').length,
      error: agents.filter(a => a.status === 'error').length,
      averageSuccessRate: agents.reduce((sum, a) => sum + (a.performance?.successRate || 0), 0) / agents.length || 0,
      totalTasksCompleted: agents.reduce((sum, a) => sum + (a.tasksCompleted || 0), 0),
    };
  }, [query.data]);

  return {
    agents: query.data || [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
    isFetching: query.isFetching,
    computedData,
  };
};

// Hook para um agente específico
export const useAgent = (id: string, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: AGENTS_QUERY_KEYS.detail(id),
    queryFn: async () => {
      const response = await apiService.get<Agent>(`/api/v1/agents/${id}`);
      return response.data;
    },
    enabled: !!id && options?.enabled !== false,
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });
};

// Hook para performance de um agente
export const useAgentPerformance = (id: string, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: AGENTS_QUERY_KEYS.performance(id),
    queryFn: async () => {
      const response = await apiService.get(`/api/v1/agents/${id}/performance`);
      return response.data;
    },
    enabled: !!id && options?.enabled !== false,
    staleTime: 1 * 60 * 1000, // 1 minuto (dados de performance mudam mais frequentemente)
    gcTime: 3 * 60 * 1000,
    refetchInterval: 30 * 1000, // Refetch a cada 30 segundos
  });
};

// Hook para criar agente
export const useCreateAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateAgentData) => {
      const response = await apiService.post<Agent>('/api/v1/agents', data);
      return response.data;
    },
    onSuccess: (newAgent) => {
      // Invalidar todas as listas de agentes
      queryClient.invalidateQueries({ queryKey: AGENTS_QUERY_KEYS.lists() });
      
      // Adicionar o novo agente ao cache
      queryClient.setQueryData(AGENTS_QUERY_KEYS.detail(newAgent.id), newAgent);
      
      toast({
        title: "Agente criado com sucesso",
        description: `${newAgent.name} foi criado e está pronto para uso.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Erro ao criar agente",
        description: error.message || "Ocorreu um erro inesperado.",
        variant: "destructive",
      });
    },
  });
};

// Hook para atualizar agente
export const useUpdateAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateAgentData }) => {
      const response = await apiService.put<Agent>(`/api/v1/agents/${id}`, data);
      return response.data;
    },
    onMutate: async ({ id, data }) => {
      // Cancelar queries em andamento
      await queryClient.cancelQueries({ queryKey: AGENTS_QUERY_KEYS.detail(id) });
      
      // Snapshot do estado anterior
      const previousAgent = queryClient.getQueryData<Agent>(AGENTS_QUERY_KEYS.detail(id));
      
      // Optimistic update
      if (previousAgent) {
        queryClient.setQueryData<Agent>(AGENTS_QUERY_KEYS.detail(id), {
          ...previousAgent,
          ...data,
          updatedAt: new Date().toISOString(),
        });
      }
      
      return { previousAgent };
    },
    onError: (error: any, variables, context) => {
      // Reverter optimistic update
      if (context?.previousAgent) {
        queryClient.setQueryData(AGENTS_QUERY_KEYS.detail(variables.id), context.previousAgent);
      }
      
      toast({
        title: "Erro ao atualizar agente",
        description: error.message || "Ocorreu um erro inesperado.",
        variant: "destructive",
      });
    },
    onSuccess: (updatedAgent) => {
      // Invalidar listas para refletir mudanças
      queryClient.invalidateQueries({ queryKey: AGENTS_QUERY_KEYS.lists() });
      
      toast({
        title: "Agente atualizado",
        description: `${updatedAgent.name} foi atualizado com sucesso.`,
      });
    },
    onSettled: (data, error, variables) => {
      // Sempre refetch o agente específico
      queryClient.invalidateQueries({ queryKey: AGENTS_QUERY_KEYS.detail(variables.id) });
    },
  });
};

// Hook para deletar agente
export const useDeleteAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await apiService.delete(`/api/v1/agents/${id}`);
      return id;
    },
    onMutate: async (id) => {
      // Cancelar queries relacionadas
      await queryClient.cancelQueries({ queryKey: AGENTS_QUERY_KEYS.detail(id) });
      
      // Snapshot do agente
      const previousAgent = queryClient.getQueryData<Agent>(AGENTS_QUERY_KEYS.detail(id));
      
      // Remover das listas (optimistic update)
      queryClient.setQueriesData<Agent[]>(
        { queryKey: AGENTS_QUERY_KEYS.lists() },
        (old) => old?.filter(agent => agent.id !== id) || []
      );
      
      return { previousAgent };
    },
    onError: (error: any, id, context) => {
      // Reverter optimistic update
      if (context?.previousAgent) {
        queryClient.setQueryData(AGENTS_QUERY_KEYS.detail(id), context.previousAgent);
      }
      
      // Invalidar listas para restaurar estado
      queryClient.invalidateQueries({ queryKey: AGENTS_QUERY_KEYS.lists() });
      
      toast({
        title: "Erro ao deletar agente",
        description: error.message || "Ocorreu um erro inesperado.",
        variant: "destructive",
      });
    },
    onSuccess: (id) => {
      // Remover do cache
      queryClient.removeQueries({ queryKey: AGENTS_QUERY_KEYS.detail(id) });
      
      toast({
        title: "Agente deletado",
        description: "O agente foi removido permanentemente.",
      });
    },
    onSettled: () => {
      // Invalidar listas para garantir consistência
      queryClient.invalidateQueries({ queryKey: AGENTS_QUERY_KEYS.lists() });
    },
  });
};

// Hook para ações rápidas de status
export const useAgentStatusActions = () => {
  const updateAgent = useUpdateAgent();
  
  const toggleStatus = useCallback((id: string, currentStatus: Agent['status']) => {
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    updateAgent.mutate({ id, data: { status: newStatus } });
  }, [updateAgent]);
  
  const activateAgent = useCallback((id: string) => {
    updateAgent.mutate({ id, data: { status: 'active' } });
  }, [updateAgent]);
  
  const deactivateAgent = useCallback((id: string) => {
    updateAgent.mutate({ id, data: { status: 'inactive' } });
  }, [updateAgent]);
  
  return {
    toggleStatus,
    activateAgent,
    deactivateAgent,
    isUpdating: updateAgent.isPending,
  };
};

// Hook para prefetch de agentes
export const usePrefetchAgents = () => {
  const queryClient = useQueryClient();
  
  const prefetchAgents = useCallback((filters?: Record<string, any>) => {
    queryClient.prefetchQuery({
      queryKey: AGENTS_QUERY_KEYS.list(filters || {}),
      queryFn: async () => {
        const params = new URLSearchParams();
        if (filters) {
          Object.entries(filters).forEach(([key, value]) => {
            if (value) params.append(key, value.toString());
          });
        }
        
        const response = await apiService.get<Agent[]>(`/api/v1/agents?${params.toString()}`);
        return response.data;
      },
      staleTime: 5 * 60 * 1000,
    });
  }, [queryClient]);
  
  const prefetchAgent = useCallback((id: string) => {
    queryClient.prefetchQuery({
      queryKey: AGENTS_QUERY_KEYS.detail(id),
      queryFn: async () => {
        const response = await apiService.get<Agent>(`/api/v1/agents/${id}`);
        return response.data;
      },
      staleTime: 2 * 60 * 1000,
    });
  }, [queryClient]);
  
  return {
    prefetchAgents,
    prefetchAgent,
  };
};
