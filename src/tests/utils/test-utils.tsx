/**
 * Utilities para testes do frontend
 * Wrappers customizados e helpers para React Testing Library
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { useAppStore } from '@/stores/useAppStore';
import type { User, Agent, Task, Campaign } from '@/stores/types';

// Configuração de QueryClient para testes
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: console.log,
      warn: console.warn,
      error: () => {}, // Silenciar erros em testes
    },
  });

// Interface para opções de render customizado
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialEntries?: string[];
  queryClient?: QueryClient;
  initialStoreState?: Partial<ReturnType<typeof useAppStore.getState>>;
}

// Wrapper customizado para testes
const AllTheProviders: React.FC<{
  children: React.ReactNode;
  queryClient: QueryClient;
  initialEntries?: string[];
  initialStoreState?: Partial<ReturnType<typeof useAppStore.getState>>;
}> = ({ children, queryClient, initialEntries = ['/'], initialStoreState }) => {
  // Configurar estado inicial do store se fornecido
  React.useEffect(() => {
    if (initialStoreState) {
      const store = useAppStore.getState();
      
      // Aplicar estado inicial
      if (initialStoreState.user !== undefined) {
        store.actions.setUser(initialStoreState.user);
      }
      if (initialStoreState.agents) {
        store.actions.setAgents(initialStoreState.agents);
      }
      if (initialStoreState.tasks) {
        store.actions.setTasks(initialStoreState.tasks);
      }
      if (initialStoreState.campaigns) {
        store.actions.setCampaigns(initialStoreState.campaigns);
      }
    }
  }, [initialStoreState]);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

// Função de render customizada
const customRender = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
): RenderResult => {
  const {
    initialEntries,
    queryClient = createTestQueryClient(),
    initialStoreState,
    ...renderOptions
  } = options;

  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <AllTheProviders
      queryClient={queryClient}
      initialEntries={initialEntries}
      initialStoreState={initialStoreState}
    >
      {children}
    </AllTheProviders>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Dados de teste padrão
export const mockUser: User = {
  id: 'test-user-1',
  email: 'test@example.com',
  firstName: 'John',
  lastName: 'Doe',
  company: 'Test Corp',
  status: 'active',
  subscriptionType: 'pro',
  subscriptionExpiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
  lastLogin: new Date().toISOString(),
  loginCount: 42,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

export const mockAgents: Agent[] = [
  {
    id: 'agent-1',
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
    userId: 'test-user-1',
  },
  {
    id: 'agent-2',
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
    userId: 'test-user-1',
  },
  {
    id: 'agent-3',
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
    userId: 'test-user-1',
  },
];

export const mockTasks: Task[] = [
  {
    id: 'task-1',
    agentId: 'agent-1',
    type: 'Campaign Analysis',
    status: 'completed',
    input: { campaign_id: 'camp_123' },
    output: { analysis: 'Campaign performing well' },
    executionTime: 1250,
    createdAt: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'task-2',
    agentId: 'agent-2',
    type: 'Customer Query',
    status: 'running',
    input: { query: 'How to reset password?' },
    createdAt: new Date(Date.now() - 30 * 1000).toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'task-3',
    agentId: 'agent-1',
    type: 'Ad Optimization',
    status: 'failed',
    input: { ad_id: 'ad_456' },
    error: 'API rate limit exceeded',
    createdAt: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

export const mockCampaigns: Campaign[] = [
  {
    id: 'campaign-1',
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
    userId: 'test-user-1',
  },
  {
    id: 'campaign-2',
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
    userId: 'test-user-1',
  },
];

// Helper para criar estado inicial do store
export const createMockStoreState = (overrides: any = {}) => ({
  user: mockUser,
  isAuthenticated: true,
  agents: mockAgents,
  tasks: mockTasks,
  campaigns: mockCampaigns,
  loading: {
    user: false,
    agents: false,
    tasks: false,
    campaigns: false,
    dashboard: false,
  },
  errors: {},
  ...overrides,
});

// Helper para aguardar elementos assíncronos
export const waitForLoadingToFinish = () =>
  new Promise((resolve) => setTimeout(resolve, 0));

// Helper para simular delay
export const delay = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));

// Helper para criar eventos de usuário
export const createUserEvent = () => {
  const userEvent = require('@testing-library/user-event').default;
  return userEvent.setup();
};

// Helper para verificar acessibilidade
export const checkAccessibility = async (container: HTMLElement) => {
  const { axe, toHaveNoViolations } = await import('jest-axe');
  expect.extend(toHaveNoViolations);
  
  const results = await axe(container);
  expect(results).toHaveNoViolations();
};

// Helper para capturar console.error em testes
export const suppressConsoleError = (callback: () => void) => {
  const originalError = console.error;
  console.error = jest.fn();
  
  try {
    callback();
  } finally {
    console.error = originalError;
  }
};

// Helper para testar hooks
export const renderHook = (hook: () => any, options: CustomRenderOptions = {}) => {
  const { result, rerender, unmount } = require('@testing-library/react').renderHook(
    hook,
    {
      wrapper: ({ children }: { children: React.ReactNode }) => (
        <AllTheProviders
          queryClient={options.queryClient || createTestQueryClient()}
          initialEntries={options.initialEntries}
          initialStoreState={options.initialStoreState}
        >
          {children}
        </AllTheProviders>
      ),
    }
  );
  
  return { result, rerender, unmount };
};

// Re-exportar tudo do testing-library
export * from '@testing-library/react';
export { customRender as render };
export { createTestQueryClient };
