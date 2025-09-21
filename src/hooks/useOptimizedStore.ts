import { useCallback, useMemo } from 'react';
import { shallow } from 'zustand/shallow';
import { useAppStore } from '@/stores/useAppStore';
import type { Agent, Task, Campaign } from '@/stores/types';

/**
 * Hooks otimizados para evitar re-renders desnecessários
 * Usa shallow comparison e memoização para máxima performance
 */

// Hook para dados do usuário com shallow comparison
export const useUserData = () => {
  return useAppStore(
    (state) => ({
      user: state.user,
      isAuthenticated: state.isAuthenticated,
      loading: state.loading.user,
      error: state.errors.user,
    }),
    shallow
  );
};

// Hook para agentes com filtros aplicados
export const useFilteredAgents = () => {
  return useAppStore((state) => {
    const { agents, filters } = state;
    const { status, type, search } = filters.agents;

    return agents.filter((agent) => {
      if (status && agent.status !== status) return false;
      if (type && agent.type !== type) return false;
      if (search) {
        const searchLower = search.toLowerCase();
        return (
          agent.name.toLowerCase().includes(searchLower) ||
          agent.type.toLowerCase().includes(searchLower) ||
          agent.description?.toLowerCase().includes(searchLower)
        );
      }
      return true;
    });
  }, shallow);
};

// Hook para tasks com filtros e paginação
export const useFilteredTasks = () => {
  return useAppStore((state) => {
    const { tasks, filters, pagination } = state;
    const { status, agentId, dateRange } = filters.tasks;
    const { page, pageSize } = pagination.tasks;

    let filteredTasks = tasks.filter((task) => {
      if (status && task.status !== status) return false;
      if (agentId && task.agentId !== agentId) return false;
      if (dateRange) {
        const taskDate = new Date(task.createdAt);
        const startDate = new Date(dateRange.start);
        const endDate = new Date(dateRange.end);
        if (taskDate < startDate || taskDate > endDate) return false;
      }
      return true;
    });

    // Aplicar paginação
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedTasks = filteredTasks.slice(startIndex, endIndex);

    return {
      tasks: paginatedTasks,
      total: filteredTasks.length,
      hasNext: endIndex < filteredTasks.length,
      hasPrevious: page > 1,
    };
  }, shallow);
};

// Hook para campanhas ativas com métricas
export const useCampaignMetrics = () => {
  return useAppStore((state) => {
    const activeCampaigns = state.campaigns.filter((c) => c.status === 'active');
    
    const metrics = activeCampaigns.reduce(
      (acc, campaign) => ({
        totalBudget: acc.totalBudget + campaign.budget,
        totalSpent: acc.totalSpent + campaign.spent,
        totalImpressions: acc.totalImpressions + campaign.impressions,
        totalClicks: acc.totalClicks + campaign.clicks,
        totalConversions: acc.totalConversions + campaign.conversions,
      }),
      {
        totalBudget: 0,
        totalSpent: 0,
        totalImpressions: 0,
        totalClicks: 0,
        totalConversions: 0,
      }
    );

    return {
      ...metrics,
      activeCampaigns: activeCampaigns.length,
      avgCTR: metrics.totalImpressions > 0 
        ? (metrics.totalClicks / metrics.totalImpressions) * 100 
        : 0,
      avgCVR: metrics.totalClicks > 0 
        ? (metrics.totalConversions / metrics.totalClicks) * 100 
        : 0,
      budgetUtilization: metrics.totalBudget > 0 
        ? (metrics.totalSpent / metrics.totalBudget) * 100 
        : 0,
    };
  }, shallow);
};

// Hook para estatísticas do dashboard
export const useDashboardStats = () => {
  return useAppStore((state) => {
    const { agents, tasks, campaigns, metrics } = state;
    
    const today = new Date().toDateString();
    const todayTasks = tasks.filter(
      (task) => new Date(task.createdAt).toDateString() === today
    );
    
    const completedToday = todayTasks.filter((task) => task.status === 'completed');
    const failedToday = todayTasks.filter((task) => task.status === 'failed');
    
    return {
      totalAgents: agents.length,
      activeAgents: agents.filter((a) => a.status === 'active').length,
      totalTasks: tasks.length,
      runningTasks: tasks.filter((t) => t.status === 'running').length,
      todayTasks: todayTasks.length,
      completedToday: completedToday.length,
      failedToday: failedToday.length,
      successRate: todayTasks.length > 0 
        ? (completedToday.length / todayTasks.length) * 100 
        : 0,
      activeCampaigns: campaigns.filter((c) => c.status === 'active').length,
      totalCampaigns: campaigns.length,
      realtimeMetrics: metrics,
    };
  }, shallow);
};

// Hook para notificações não lidas
export const useUnreadNotifications = () => {
  return useAppStore((state) => {
    const unread = state.notifications.filter((n) => !n.read);
    return {
      notifications: unread,
      count: unread.length,
      hasUnread: unread.length > 0,
    };
  }, shallow);
};

// Hook para estado de loading específico
export const useLoadingState = (keys: (keyof typeof useAppStore.getState.loading)[]) => {
  return useAppStore((state) => {
    const loadingStates = keys.reduce((acc, key) => {
      acc[key] = state.loading[key];
      return acc;
    }, {} as Record<string, boolean>);
    
    return {
      ...loadingStates,
      isAnyLoading: Object.values(loadingStates).some(Boolean),
    };
  }, shallow);
};

// Hook para erros específicos
export const useErrorState = (keys: (keyof typeof useAppStore.getState.errors)[]) => {
  return useAppStore((state) => {
    const errorStates = keys.reduce((acc, key) => {
      acc[key] = state.errors[key];
      return acc;
    }, {} as Record<string, string | undefined>);
    
    return {
      ...errorStates,
      hasAnyError: Object.values(errorStates).some(Boolean),
    };
  }, shallow);
};

// Hook para ações memoizadas
export const useStoreActions = () => {
  const actions = useAppStore((state) => state.actions);
  
  // Memoizar ações para evitar re-renders
  const memoizedActions = useMemo(() => ({
    // User actions
    setUser: actions.setUser,
    updateUser: actions.updateUser,
    logout: actions.logout,
    
    // Agent actions
    addAgent: actions.addAgent,
    updateAgent: actions.updateAgent,
    removeAgent: actions.removeAgent,
    
    // Task actions
    addTask: actions.addTask,
    updateTask: actions.updateTask,
    removeTask: actions.removeTask,
    
    // Campaign actions
    addCampaign: actions.addCampaign,
    updateCampaign: actions.updateCampaign,
    removeCampaign: actions.removeCampaign,
    
    // Notification actions
    addNotification: actions.addNotification,
    markNotificationRead: actions.markNotificationRead,
    removeNotification: actions.removeNotification,
    
    // UI actions
    toggleSidebar: actions.toggleSidebar,
    openModal: actions.openModal,
    closeModal: actions.closeModal,
    setBreadcrumbs: actions.setBreadcrumbs,
    
    // Loading/Error actions
    setLoading: actions.setLoading,
    setError: actions.setError,
    clearErrors: actions.clearErrors,
  }), [actions]);
  
  return memoizedActions;
};

// Hook para performance de agentes
export const useAgentPerformance = (agentId?: string) => {
  return useAppStore((state) => {
    if (!agentId) return null;
    
    const agent = state.agents.find((a) => a.id === agentId);
    if (!agent) return null;
    
    const agentTasks = state.tasks.filter((t) => t.agentId === agentId);
    const completedTasks = agentTasks.filter((t) => t.status === 'completed');
    const failedTasks = agentTasks.filter((t) => t.status === 'failed');
    
    const avgExecutionTime = completedTasks.length > 0
      ? completedTasks.reduce((sum, task) => sum + (task.executionTime || 0), 0) / completedTasks.length
      : 0;
    
    return {
      agent,
      totalTasks: agentTasks.length,
      completedTasks: completedTasks.length,
      failedTasks: failedTasks.length,
      successRate: agentTasks.length > 0 
        ? (completedTasks.length / agentTasks.length) * 100 
        : 0,
      avgExecutionTime,
      isActive: agent.status === 'active',
      lastActivity: agent.lastActivity,
    };
  }, shallow);
};

// Hook para busca otimizada
export const useSearch = () => {
  const setAgentFilters = useAppStore((state) => state.actions.setAgentFilters);
  const setTaskFilters = useAppStore((state) => state.actions.setTaskFilters);
  const setCampaignFilters = useAppStore((state) => state.actions.setCampaignFilters);
  
  const searchAgents = useCallback((query: string) => {
    setAgentFilters({ search: query });
  }, [setAgentFilters]);
  
  const searchCampaigns = useCallback((query: string) => {
    setCampaignFilters({ search: query });
  }, [setCampaignFilters]);
  
  return {
    searchAgents,
    searchCampaigns,
  };
};

// Hook para tema e configurações de UI
export const useTheme = () => {
  return useAppStore((state) => ({
    theme: state.settings.theme,
    updateTheme: (theme: 'light' | 'dark' | 'system') => 
      state.actions.updateSettings({ theme }),
  }), shallow);
};

// Hook para breadcrumbs
export const useBreadcrumbs = () => {
  return useAppStore((state) => ({
    breadcrumbs: state.ui.breadcrumbs,
    setBreadcrumbs: state.actions.setBreadcrumbs,
  }), shallow);
};

// Hook para sidebar
export const useSidebar = () => {
  return useAppStore((state) => ({
    isOpen: state.ui.sidebarOpen,
    isCollapsed: state.ui.sidebarCollapsed,
    toggle: state.actions.toggleSidebar,
    setCollapsed: state.actions.setSidebarCollapsed,
  }), shallow);
};
