// Types para o sistema de estado global

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  company?: string;
  status: 'active' | 'inactive' | 'suspended' | 'pending_verification';
  subscriptionType: 'free' | 'basic' | 'pro' | 'enterprise';
  subscriptionExpiresAt?: string;
  lastLogin?: string;
  loginCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'inactive' | 'paused' | 'error';
  description?: string;
  configuration: Record<string, any>;
  tasksCompleted: number;
  successRate: number;
  lastActivity?: string;
  createdAt: string;
  updatedAt: string;
  userId: string;
}

export interface Task {
  id: string;
  agentId: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  input: Record<string, any>;
  output?: Record<string, any>;
  error?: string;
  executionTime?: number;
  createdAt: string;
  updatedAt: string;
}

export interface Campaign {
  id: string;
  name: string;
  platform: 'google_ads' | 'meta_ads' | 'tiktok_ads';
  status: 'active' | 'paused' | 'completed' | 'draft';
  budget: number;
  spent: number;
  impressions: number;
  clicks: number;
  conversions: number;
  startDate: string;
  endDate?: string;
  createdAt: string;
  updatedAt: string;
  userId: string;
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
  expiresAt?: string;
}

// Estado de loading para diferentes operações
export interface LoadingState {
  user: boolean;
  agents: boolean;
  tasks: boolean;
  campaigns: boolean;
  dashboard: boolean;
}

// Estado de erro
export interface ErrorState {
  user?: string;
  agents?: string;
  tasks?: string;
  campaigns?: string;
  dashboard?: string;
  global?: string;
}

// Filtros e paginação
export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface FilterState {
  agents: {
    status?: Agent['status'];
    type?: string;
    search?: string;
  };
  tasks: {
    status?: Task['status'];
    agentId?: string;
    dateRange?: {
      start: string;
      end: string;
    };
  };
  campaigns: {
    status?: Campaign['status'];
    platform?: Campaign['platform'];
    search?: string;
  };
}

// Configurações da aplicação
export interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  language: 'en' | 'pt' | 'es';
  notifications: {
    email: boolean;
    push: boolean;
    desktop: boolean;
  };
  dashboard: {
    refreshInterval: number;
    defaultView: 'overview' | 'agents' | 'campaigns';
  };
}

// Estado de UI
export interface UIState {
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  activeModal?: string;
  activeSheet?: string;
  breadcrumbs: Array<{
    label: string;
    href?: string;
  }>;
}

// Métricas em tempo real
export interface RealtimeMetrics {
  activeAgents: number;
  runningTasks: number;
  todayTasks: number;
  todayRevenue: number;
  lastUpdated: string;
}
