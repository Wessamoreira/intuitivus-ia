/**
 * UI Store - Gerenciamento de Estado da Interface
 * Store Zustand focado exclusivamente no estado da UI
 */

import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

export type Theme = 'light' | 'dark' | 'system';
export type SidebarState = 'expanded' | 'collapsed' | 'hidden';

export interface UIState {
  // Tema e aparência
  theme: Theme;
  sidebarState: SidebarState;
  
  // Modais e overlays
  modals: {
    createAgent: boolean;
    editAgent: boolean;
    createTask: boolean;
    editTask: boolean;
    createCampaign: boolean;
    editCampaign: boolean;
    userProfile: boolean;
    settings: boolean;
  };
  
  // Estados de loading da UI (não de dados)
  uiLoading: {
    sidebarToggle: boolean;
    themeChange: boolean;
    modalTransition: boolean;
  };
  
  // Filtros e ordenação (estado da UI, não dados)
  filters: {
    agents: {
      status: string;
      type: string;
      sortBy: string;
      sortOrder: 'asc' | 'desc';
      searchTerm: string;
    };
    tasks: {
      status: string;
      priority: string;
      agentId: string;
      sortBy: string;
      sortOrder: 'asc' | 'desc';
      searchTerm: string;
    };
    campaigns: {
      status: string;
      sortBy: string;
      sortOrder: 'asc' | 'desc';
      searchTerm: string;
    };
  };
  
  // Layout e visualização
  layout: {
    dashboardView: 'grid' | 'list' | 'table';
    agentsView: 'grid' | 'list';
    tasksView: 'list' | 'kanban';
    campaignsView: 'grid' | 'table';
  };
  
  // Notificações da UI
  notifications: {
    show: boolean;
    position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
    autoHide: boolean;
    duration: number;
  };
  
  // Breadcrumbs e navegação
  navigation: {
    currentPage: string;
    breadcrumbs: Array<{ label: string; href: string }>;
    previousPage: string | null;
  };
  
  // Estados de formulários
  forms: {
    isDirty: boolean;
    hasUnsavedChanges: boolean;
    currentForm: string | null;
  };
  
  // Actions
  actions: {
    // Tema
    setTheme: (theme: Theme) => void;
    toggleTheme: () => void;
    
    // Sidebar
    setSidebarState: (state: SidebarState) => void;
    toggleSidebar: () => void;
    
    // Modais
    openModal: (modal: keyof UIState['modals']) => void;
    closeModal: (modal: keyof UIState['modals']) => void;
    closeAllModals: () => void;
    
    // Loading states
    setUILoading: (key: keyof UIState['uiLoading'], loading: boolean) => void;
    
    // Filtros
    setAgentFilter: (key: keyof UIState['filters']['agents'], value: string) => void;
    setTaskFilter: (key: keyof UIState['filters']['tasks'], value: string) => void;
    setCampaignFilter: (key: keyof UIState['filters']['campaigns'], value: string) => void;
    clearFilters: (entity: 'agents' | 'tasks' | 'campaigns') => void;
    
    // Layout
    setDashboardView: (view: UIState['layout']['dashboardView']) => void;
    setAgentsView: (view: UIState['layout']['agentsView']) => void;
    setTasksView: (view: UIState['layout']['tasksView']) => void;
    setCampaignsView: (view: UIState['layout']['campaignsView']) => void;
    
    // Navegação
    setCurrentPage: (page: string) => void;
    setBreadcrumbs: (breadcrumbs: UIState['navigation']['breadcrumbs']) => void;
    
    // Formulários
    setFormDirty: (isDirty: boolean) => void;
    setUnsavedChanges: (hasChanges: boolean) => void;
    setCurrentForm: (form: string | null) => void;
    
    // Reset
    resetUI: () => void;
  };
}

const initialState = {
  theme: 'system' as Theme,
  sidebarState: 'expanded' as SidebarState,
  
  modals: {
    createAgent: false,
    editAgent: false,
    createTask: false,
    editTask: false,
    createCampaign: false,
    editCampaign: false,
    userProfile: false,
    settings: false,
  },
  
  uiLoading: {
    sidebarToggle: false,
    themeChange: false,
    modalTransition: false,
  },
  
  filters: {
    agents: {
      status: '',
      type: '',
      sortBy: 'name',
      sortOrder: 'asc' as const,
      searchTerm: '',
    },
    tasks: {
      status: '',
      priority: '',
      agentId: '',
      sortBy: 'createdAt',
      sortOrder: 'desc' as const,
      searchTerm: '',
    },
    campaigns: {
      status: '',
      sortBy: 'createdAt',
      sortOrder: 'desc' as const,
      searchTerm: '',
    },
  },
  
  layout: {
    dashboardView: 'grid' as const,
    agentsView: 'grid' as const,
    tasksView: 'list' as const,
    campaignsView: 'grid' as const,
  },
  
  notifications: {
    show: true,
    position: 'top-right' as const,
    autoHide: true,
    duration: 5000,
  },
  
  navigation: {
    currentPage: '',
    breadcrumbs: [],
    previousPage: null,
  },
  
  forms: {
    isDirty: false,
    hasUnsavedChanges: false,
    currentForm: null,
  },
};

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      subscribeWithSelector(
        immer((set, get) => ({
          ...initialState,
          
          actions: {
            // Tema
            setTheme: (theme: Theme) => {
              set((state) => {
                state.theme = theme;
              });
            },
            
            toggleTheme: () => {
              set((state) => {
                const currentTheme = state.theme;
                state.theme = currentTheme === 'light' ? 'dark' : 'light';
              });
            },
            
            // Sidebar
            setSidebarState: (sidebarState: SidebarState) => {
              set((state) => {
                state.sidebarState = sidebarState;
              });
            },
            
            toggleSidebar: () => {
              set((state) => {
                state.sidebarState = state.sidebarState === 'expanded' ? 'collapsed' : 'expanded';
              });
            },
            
            // Modais
            openModal: (modal: keyof UIState['modals']) => {
              set((state) => {
                state.modals[modal] = true;
              });
            },
            
            closeModal: (modal: keyof UIState['modals']) => {
              set((state) => {
                state.modals[modal] = false;
              });
            },
            
            closeAllModals: () => {
              set((state) => {
                Object.keys(state.modals).forEach(key => {
                  state.modals[key as keyof UIState['modals']] = false;
                });
              });
            },
            
            // Loading states
            setUILoading: (key: keyof UIState['uiLoading'], loading: boolean) => {
              set((state) => {
                state.uiLoading[key] = loading;
              });
            },
            
            // Filtros
            setAgentFilter: (key: keyof UIState['filters']['agents'], value: string) => {
              set((state) => {
                state.filters.agents[key] = value as any;
              });
            },
            
            setTaskFilter: (key: keyof UIState['filters']['tasks'], value: string) => {
              set((state) => {
                state.filters.tasks[key] = value as any;
              });
            },
            
            setCampaignFilter: (key: keyof UIState['filters']['campaigns'], value: string) => {
              set((state) => {
                state.filters.campaigns[key] = value as any;
              });
            },
            
            clearFilters: (entity: 'agents' | 'tasks' | 'campaigns') => {
              set((state) => {
                const entityFilters = state.filters[entity];
                Object.keys(entityFilters).forEach(key => {
                  if (key === 'sortBy' || key === 'sortOrder') return;
                  (entityFilters as any)[key] = '';
                });
              });
            },
            
            // Layout
            setDashboardView: (view: UIState['layout']['dashboardView']) => {
              set((state) => {
                state.layout.dashboardView = view;
              });
            },
            
            setAgentsView: (view: UIState['layout']['agentsView']) => {
              set((state) => {
                state.layout.agentsView = view;
              });
            },
            
            setTasksView: (view: UIState['layout']['tasksView']) => {
              set((state) => {
                state.layout.tasksView = view;
              });
            },
            
            setCampaignsView: (view: UIState['layout']['campaignsView']) => {
              set((state) => {
                state.layout.campaignsView = view;
              });
            },
            
            // Navegação
            setCurrentPage: (page: string) => {
              set((state) => {
                state.navigation.previousPage = state.navigation.currentPage;
                state.navigation.currentPage = page;
              });
            },
            
            setBreadcrumbs: (breadcrumbs: UIState['navigation']['breadcrumbs']) => {
              set((state) => {
                state.navigation.breadcrumbs = breadcrumbs;
              });
            },
            
            // Formulários
            setFormDirty: (isDirty: boolean) => {
              set((state) => {
                state.forms.isDirty = isDirty;
              });
            },
            
            setUnsavedChanges: (hasChanges: boolean) => {
              set((state) => {
                state.forms.hasUnsavedChanges = hasChanges;
              });
            },
            
            setCurrentForm: (form: string | null) => {
              set((state) => {
                state.forms.currentForm = form;
              });
            },
            
            // Reset
            resetUI: () => {
              set((state) => {
                Object.assign(state, initialState);
              });
            },
          },
        }))
      ),
      {
        name: 'ui-store',
        partialize: (state) => ({
          theme: state.theme,
          sidebarState: state.sidebarState,
          layout: state.layout,
          notifications: state.notifications,
        }),
      }
    ),
    {
      name: 'ui-store',
    }
  )
);

// Selectors otimizados
export const useTheme = () => useUIStore((state) => state.theme);
export const useSidebarState = () => useUIStore((state) => state.sidebarState);
export const useModals = () => useUIStore((state) => state.modals);
export const useFilters = () => useUIStore((state) => state.filters);
export const useLayout = () => useUIStore((state) => state.layout);
export const useNavigation = () => useUIStore((state) => state.navigation);
export const useFormState = () => useUIStore((state) => state.forms);
export const useUIActions = () => useUIStore((state) => state.actions);
