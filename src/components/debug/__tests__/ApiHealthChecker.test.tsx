/**
 * Testes para o componente ApiHealthChecker
 * Equivalente aos testes de componentes React com Testing Library
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApiHealthChecker } from '../ApiHealthChecker';

// Mock dos hooks
vi.mock('@/hooks/useApiHealth', () => ({
  useApiHealth: vi.fn(),
  useConnectivityTest: vi.fn(),
}));

import { useApiHealth, useConnectivityTest } from '@/hooks/useApiHealth';

const mockUseApiHealth = vi.mocked(useApiHealth);
const mockUseConnectivityTest = vi.mocked(useConnectivityTest);

// Wrapper com QueryClient para testes
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('ApiHealthChecker', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render healthy status correctly', () => {
    mockUseApiHealth.mockReturnValue({
      healthStatus: {
        isHealthy: true,
        status: 'healthy',
        app_name: 'Intuitivus Flow Studio',
        version: '1.0.0',
        responseTime: 150,
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUseConnectivityTest.mockReturnValue({
      testResults: {
        backend: true,
        responseTime: 120,
        lastTest: null,
      },
      runConnectivityTest: vi.fn(),
    });

    render(<ApiHealthChecker />, { wrapper: createWrapper() });

    expect(screen.getByText('Conectado')).toBeInTheDocument();
    expect(screen.getByText('healthy')).toBeInTheDocument();
    expect(screen.getByText('Intuitivus Flow Studio')).toBeInTheDocument();
    expect(screen.getByText('1.0.0')).toBeInTheDocument();
    expect(screen.getByText('150ms')).toBeInTheDocument();
  });

  it('should render unhealthy status correctly', () => {
    mockUseApiHealth.mockReturnValue({
      healthStatus: {
        isHealthy: false,
        status: 'unhealthy',
        error: 'Erro de conexão com o servidor',
      },
      isLoading: false,
      isError: true,
      error: new Error('Network error'),
      refetch: vi.fn(),
    });

    mockUseConnectivityTest.mockReturnValue({
      testResults: {
        backend: false,
        responseTime: 0,
        lastTest: null,
      },
      runConnectivityTest: vi.fn(),
    });

    render(<ApiHealthChecker />, { wrapper: createWrapper() });

    expect(screen.getByText('Desconectado')).toBeInTheDocument();
    expect(screen.getByText('unhealthy')).toBeInTheDocument();
    expect(screen.getByText('Erro de conexão com o servidor')).toBeInTheDocument();
  });

  it('should show loading state', () => {
    mockUseApiHealth.mockReturnValue({
      healthStatus: {
        isHealthy: false,
        status: 'unknown',
      },
      isLoading: true,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUseConnectivityTest.mockReturnValue({
      testResults: {
        backend: false,
        responseTime: 0,
        lastTest: null,
      },
      runConnectivityTest: vi.fn(),
    });

    render(<ApiHealthChecker />, { wrapper: createWrapper() });

    const refreshButton = screen.getByRole('button', { name: /atualizar/i });
    expect(refreshButton).toBeDisabled();
  });

  it('should call refetch when refresh button is clicked', async () => {
    const mockRefetch = vi.fn();
    
    mockUseApiHealth.mockReturnValue({
      healthStatus: {
        isHealthy: true,
        status: 'healthy',
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: mockRefetch,
    });

    mockUseConnectivityTest.mockReturnValue({
      testResults: {
        backend: true,
        responseTime: 100,
        lastTest: null,
      },
      runConnectivityTest: vi.fn(),
    });

    render(<ApiHealthChecker />, { wrapper: createWrapper() });

    const refreshButton = screen.getByRole('button', { name: /atualizar/i });
    fireEvent.click(refreshButton);

    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });

  it('should run connectivity test when button is clicked', async () => {
    const mockRunConnectivityTest = vi.fn();
    
    mockUseApiHealth.mockReturnValue({
      healthStatus: {
        isHealthy: true,
        status: 'healthy',
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUseConnectivityTest.mockReturnValue({
      testResults: {
        backend: true,
        responseTime: 100,
        lastTest: null,
      },
      runConnectivityTest: mockRunConnectivityTest,
    });

    render(<ApiHealthChecker />, { wrapper: createWrapper() });

    const testButton = screen.getByRole('button', { name: /executar teste/i });
    fireEvent.click(testButton);

    expect(mockRunConnectivityTest).toHaveBeenCalledTimes(1);
  });

  it('should display connectivity test results', () => {
    const testDate = new Date('2024-01-01T12:00:00Z');
    
    mockUseApiHealth.mockReturnValue({
      healthStatus: {
        isHealthy: true,
        status: 'healthy',
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUseConnectivityTest.mockReturnValue({
      testResults: {
        backend: true,
        responseTime: 250,
        lastTest: testDate,
      },
      runConnectivityTest: vi.fn(),
    });

    render(<ApiHealthChecker />, { wrapper: createWrapper() });

    expect(screen.getByText('OK')).toBeInTheDocument();
    expect(screen.getByText('250ms')).toBeInTheDocument();
    expect(screen.getByText(testDate.toLocaleTimeString())).toBeInTheDocument();
  });

  it('should display failed connectivity test results', () => {
    const testDate = new Date('2024-01-01T12:00:00Z');
    
    mockUseApiHealth.mockReturnValue({
      healthStatus: {
        isHealthy: false,
        status: 'unhealthy',
      },
      isLoading: false,
      isError: true,
      error: new Error('Connection failed'),
      refetch: vi.fn(),
    });

    mockUseConnectivityTest.mockReturnValue({
      testResults: {
        backend: false,
        responseTime: 5000,
        lastTest: testDate,
      },
      runConnectivityTest: vi.fn(),
    });

    render(<ApiHealthChecker />, { wrapper: createWrapper() });

    expect(screen.getByText('Falha')).toBeInTheDocument();
    expect(screen.getByText('5000ms')).toBeInTheDocument();
  });

  it('should have proper accessibility attributes', () => {
    mockUseApiHealth.mockReturnValue({
      healthStatus: {
        isHealthy: true,
        status: 'healthy',
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUseConnectivityTest.mockReturnValue({
      testResults: {
        backend: true,
        responseTime: 100,
        lastTest: null,
      },
      runConnectivityTest: vi.fn(),
    });

    render(<ApiHealthChecker />, { wrapper: createWrapper() });

    const refreshButton = screen.getByRole('button', { name: /atualizar/i });
    const testButton = screen.getByRole('button', { name: /executar teste/i });

    expect(refreshButton).toBeInTheDocument();
    expect(testButton).toBeInTheDocument();
  });
});
