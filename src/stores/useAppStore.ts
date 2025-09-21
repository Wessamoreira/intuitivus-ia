import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type {
  User,
  Agent,
  Task,
  Campaign,
  Notification,
  LoadingState,
  ErrorState,
  FilterState,
  AppSettings,
  UIState,
  RealtimeMetrics,
  PaginationState
} from './types';

// Estado principal da aplicação
interface AppState {
  // Dados do usuário
  user: User | null;
  isAuthenticated: boolean;
  
  // Dados principais
  agents: Agent[];
  tasks: Task[];
  campaigns: Campaign[];
  notifications: Notification[];
  
  // Estados de loading
  loading: LoadingState;
  
  // Estados de erro
  errors: ErrorState;
  
  // Filtros e paginação
  filters: FilterState;
  pagination: {
    agents: PaginationState;
    tasks: PaginationState;
    campaigns: PaginationState;
  };
  
  // Configurações
  settings: AppSettings;
  
  // Estado da UI
  ui: UIState;
  
  // Métricas em tempo real
  metrics: RealtimeMetrics;
  
  // Ações
  actions: {
    // User actions
    setUser: (user: User | null) => void;
    updateUser: (updates: Partial<User>) => void;
    logout: () => void;
    
    // Agent actions
    setAgents: (agents: Agent[]) => void;
    addAgent: (agent: Agent) => void;
    updateAgent: (id: string, updates: Partial<Agent>) => void;
    removeAgent: (id: string) => void;
    
    // Task actions
    setTasks: (tasks: Task[]) => void;
    addTask: (task: Task) => void;
    updateTask: (id: string, updates: Partial<Task>) => void;
    removeTask: (id: string) => void;
    
    // Campaign actions
    setCampaigns: (campaigns: Campaign[]) => void;
    addCampaign: (campaign: Campaign) => void;
    updateCampaign: (id: string, updates: Partial<Campaign>) => void;
    removeCampaign: (id: string) => void;
    
    // Notification actions
    addNotification: (notification: Omit<Notification, 'id' | 'createdAt'>) => void;
    markNotificationRead: (id: string) => void;
    removeNotification: (id: string) => void;
    clearNotifications: () => void;
    
    // Loading actions
    setLoading: (key: keyof LoadingState, value: boolean) => void;
    
    // Error actions
    setError: (key: keyof ErrorState, error: string | undefined) => void;
    clearErrors: () => void;
    
    // Filter actions
    setAgentFilters: (filters: Partial<FilterState['agents']>) => void;
    setTaskFilters: (filters: Partial<FilterState['tasks']>) => void;
    setCampaignFilters: (filters: Partial<FilterState['campaigns']>) => void;
    clearFilters: () => void;
    
    // Pagination actions
    setAgentPagination: (pagination: Partial<PaginationState>) => void;
    setTaskPagination: (pagination: Partial<PaginationState>) => void;
    setCampaignPagination: (pagination: Partial<PaginationState>) => void;
    
    // Settings actions
    updateSettings: (updates: Partial<AppSettings>) => void;
    
    // UI actions
    toggleSidebar: () => void;
    setSidebarCollapsed: (collapsed: boolean) => void;
    openModal: (modalId: string) => void;
    closeModal: () => void;
    openSheet: (sheetId: string) => void;
    closeSheet: () => void;
    setBreadcrumbs: (breadcrumbs: UIState['breadcrumbs']) => void;
    
    // Metrics actions
    updateMetrics: (metrics: Partial<RealtimeMetrics>) => void;
    
    // Utility actions
    reset: () => void;
  };
}

// Estado inicial
const initialState = {
  user: null,
  isAuthenticated: false,
  agents: [],
  tasks: [],
  campaigns: [],
  notifications: [],
  loading: {
    user: false,
    agents: false,
    tasks: false,
    campaigns: false,
    dashboard: false,
  },
  errors: {},
  filters: {
    agents: {},
    tasks: {},
    campaigns: {},
  },
  pagination: {
    agents: {
      page: 1,
      pageSize: 20,
      total: 0,
      hasNext: false,
      hasPrevious: false,
    },
    tasks: {
      page: 1,
      pageSize: 20,
      total: 0,
      hasNext: false,
      hasPrevious: false,
    },
    campaigns: {
      page: 1,
      pageSize: 20,
      total: 0,
      hasNext: false,
      hasPrevious: false,
    },
  },
  settings: {
    theme: 'system' as const,
    language: 'en' as const,
    notifications: {
      email: true,
      push: true,
      desktop: false,
    },
    dashboard: {
      refreshInterval: 30000, // 30 segundos
      defaultView: 'overview' as const,
    },
  },
  ui: {
    sidebarOpen: true,
    sidebarCollapsed: false,
    breadcrumbs: [],
  },
  metrics: {
    activeAgents: 0,
    runningTasks: 0,
    todayTasks: 0,
    todayRevenue: 0,
    lastUpdated: new Date().toISOString(),
  },
};

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      subscribeWithSelector(
        immer((set, get) => ({
          ...initialState,
          
          actions: {
            // User actions
            setUser: (user) =>
              set((state) => {
                state.user = user;
                state.isAuthenticated = !!user;
              }),
            
            updateUser: (updates) =>
              set((state) => {
                if (state.user) {
                  Object.assign(state.user, updates);
                }
              }),
            
            logout: () =>
              set((state) => {
                state.user = null;
                state.isAuthenticated = false;
                state.agents = [];
                state.tasks = [];
                state.campaigns = [];
                state.notifications = [];
              }),
            
            // Agent actions
            setAgents: (agents) =>
              set((state) => {
                state.agents = agents;
              }),
            
            addAgent: (agent) =>
              set((state) => {
                state.agents.push(agent);
              }),
            
            updateAgent: (id, updates) =>
              set((state) => {
                const index = state.agents.findIndex((a) => a.id === id);
                if (index !== -1) {
                  Object.assign(state.agents[index], updates);
                }
              }),
            
            removeAgent: (id) =>
              set((state) => {
                state.agents = state.agents.filter((a) => a.id !== id);
              }),
            
            // Task actions
            setTasks: (tasks) =>
              set((state) => {
                state.tasks = tasks;
              }),
            
            addTask: (task) =>
              set((state) => {
                state.tasks.unshift(task); // Adicionar no início
              }),
            
            updateTask: (id, updates) =>
              set((state) => {
                const index = state.tasks.findIndex((t) => t.id === id);
                if (index !== -1) {
                  Object.assign(state.tasks[index], updates);
                }
              }),
            
            removeTask: (id) =>
              set((state) => {
                state.tasks = state.tasks.filter((t) => t.id !== id);
              }),
            
            // Campaign actions
            setCampaigns: (campaigns) =>
              set((state) => {
                state.campaigns = campaigns;
              }),
            
            addCampaign: (campaign) =>
              set((state) => {
                state.campaigns.push(campaign);
              }),
            
            updateCampaign: (id, updates) =>
              set((state) => {
                const index = state.campaigns.findIndex((c) => c.id === id);
                if (index !== -1) {
                  Object.assign(state.campaigns[index], updates);
                }
              }),
            
            removeCampaign: (id) =>
              set((state) => {
                state.campaigns = state.campaigns.filter((c) => c.id !== id);
              }),
            
            // Notification actions
            addNotification: (notification) =>
              set((state) => {
                const newNotification: Notification = {
                  ...notification,
                  id: crypto.randomUUID(),
                  read: false,
                  createdAt: new Date().toISOString(),
                };
                state.notifications.unshift(newNotification);
                
                // Manter apenas últimas 50 notificações
                if (state.notifications.length > 50) {
                  state.notifications = state.notifications.slice(0, 50);
                }
              }),
            
            markNotificationRead: (id) =>
              set((state) => {
                const notification = state.notifications.find((n) => n.id === id);
                if (notification) {
                  notification.read = true;
                }
              }),
            
            removeNotification: (id) =>
              set((state) => {
                state.notifications = state.notifications.filter((n) => n.id !== id);
              }),
            
            clearNotifications: () =>
              set((state) => {
                state.notifications = [];
              }),
            
            // Loading actions
            setLoading: (key, value) =>
              set((state) => {
                state.loading[key] = value;
              }),
            
            // Error actions
            setError: (key, error) =>
              set((state) => {
                if (error) {
                  state.errors[key] = error;
                } else {
                  delete state.errors[key];
                }
              }),
            
            clearErrors: () =>
              set((state) => {
                state.errors = {};
              }),
            
            // Filter actions
            setAgentFilters: (filters) =>
              set((state) => {
                Object.assign(state.filters.agents, filters);
              }),
            
            setTaskFilters: (filters) =>
              set((state) => {
                Object.assign(state.filters.tasks, filters);
              }),
            
            setCampaignFilters: (filters) =>
              set((state) => {
                Object.assign(state.filters.campaigns, filters);
              }),
            
            clearFilters: () =>
              set((state) => {
                state.filters = {
                  agents: {},
                  tasks: {},
                  campaigns: {},
                };
              }),
            
            // Pagination actions
            setAgentPagination: (pagination) =>
              set((state) => {
                Object.assign(state.pagination.agents, pagination);
              }),
            
            setTaskPagination: (pagination) =>
              set((state) => {
                Object.assign(state.pagination.tasks, pagination);
              }),
            
            setCampaignPagination: (pagination) =>
              set((state) => {
                Object.assign(state.pagination.campaigns, pagination);
              }),
            
            // Settings actions
            updateSettings: (updates) =>
              set((state) => {
                Object.assign(state.settings, updates);
              }),
            
            // UI actions
            toggleSidebar: () =>
              set((state) => {
                state.ui.sidebarOpen = !state.ui.sidebarOpen;
              }),
            
            setSidebarCollapsed: (collapsed) =>
              set((state) => {
                state.ui.sidebarCollapsed = collapsed;
              }),
            
            openModal: (modalId) =>
              set((state) => {
                state.ui.activeModal = modalId;
              }),
            
            closeModal: () =>
              set((state) => {
                state.ui.activeModal = undefined;
              }),
            
            openSheet: (sheetId) =>
              set((state) => {
                state.ui.activeSheet = sheetId;
              }),
            
            closeSheet: () =>
              set((state) => {
                state.ui.activeSheet = undefined;
              }),
            
            setBreadcrumbs: (breadcrumbs) =>
              set((state) => {
                state.ui.breadcrumbs = breadcrumbs;
              }),
            
            // Metrics actions
            updateMetrics: (metrics) =>
              set((state) => {
                Object.assign(state.metrics, {
                  ...metrics,
                  lastUpdated: new Date().toISOString(),
                });
              }),
            
            // Utility actions
            reset: () =>
              set(() => ({
                ...initialState,
                actions: get().actions, // Manter referência das ações
              })),
          },
        }))
      ),
      {
        name: 'app-store',
        partialize: (state) => ({
          // Persistir apenas dados importantes
          user: state.user,
          isAuthenticated: state.isAuthenticated,
          settings: state.settings,
          ui: {
            sidebarCollapsed: state.ui.sidebarCollapsed,
          },
        }),
      }
    ),
    {
      name: 'app-store',
    }
  )
);

// Selectors otimizados para evitar re-renders desnecessários
export const useUser = () => useAppStore((state) => state.user);
export const useIsAuthenticated = () => useAppStore((state) => state.isAuthenticated);
export const useAgents = () => useAppStore((state) => state.agents);
export const useTasks = () => useAppStore((state) => state.tasks);
export const useCampaigns = () => useAppStore((state) => state.campaigns);
export const useNotifications = () => useAppStore((state) => state.notifications);
export const useLoading = () => useAppStore((state) => state.loading);
export const useErrors = () => useAppStore((state) => state.errors);
export const useFilters = () => useAppStore((state) => state.filters);
export const usePagination = () => useAppStore((state) => state.pagination);
export const useSettings = () => useAppStore((state) => state.settings);
export const useUI = () => useAppStore((state) => state.ui);
export const useMetrics = () => useAppStore((state) => state.metrics);
export const useActions = () => useAppStore((state) => state.actions);

// Selectors específicos
export const useActiveAgents = () =>
  useAppStore((state) => state.agents.filter((agent) => agent.status === 'active'));

export const useRunningTasks = () =>
  useAppStore((state) => state.tasks.filter((task) => task.status === 'running'));

export const useUnreadNotifications = () =>
  useAppStore((state) => state.notifications.filter((notification) => !notification.read));

export const useActiveCampaigns = () =>
  useAppStore((state) => state.campaigns.filter((campaign) => campaign.status === 'active'));

// Computed values
export const useComputedStats = () =>
  useAppStore((state) => ({
    totalAgents: state.agents.length,
    activeAgents: state.agents.filter((a) => a.status === 'active').length,
    totalTasks: state.tasks.length,
    completedTasks: state.tasks.filter((t) => t.status === 'completed').length,
    totalCampaigns: state.campaigns.length,
    activeCampaigns: state.campaigns.filter((c) => c.status === 'active').length,
    unreadNotifications: state.notifications.filter((n) => !n.read).length,
  }));
