/**
 * Hook para verificar saúde da API
 * Testa comunicação frontend-backend com AbortController
 */

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import { useAbortController, useAbortableInterval } from './useAbortController';

export interface HealthStatus {
  isHealthy: boolean;
  status: string;
  app_name?: string;
  version?: string;
  responseTime?: number;
  error?: string;
}

export const useApiHealth = (enabled: boolean = true) => {
  const [responseTime, setResponseTime] = useState<number>(0);
  const { getSignal } = useAbortController();

  const {
    data,
    error,
    isLoading,
    isError,
    refetch
  } = useQuery({
    queryKey: ['api-health'],
    queryFn: async () => {
      const signal = getSignal();
      const startTime = Date.now();
      
      try {
        const response = await apiService.get('/health', { signal });
        const endTime = Date.now();
        setResponseTime(endTime - startTime);
        return response.data;
      } catch (err: any) {
        const endTime = Date.now();
        setResponseTime(endTime - startTime);
        
        // Não tratar AbortError como erro real
        if (err.name === 'AbortError') {
          console.log('Health check aborted');
          return null;
        }
        
        throw err;
      }
    },
    enabled,
    refetchInterval: 30000, // Refetch a cada 30 segundos
    retry: (failureCount, error: any) => {
      // Não tentar novamente se foi abortado
      if (error?.name === 'AbortError') return false;
      return failureCount < 3;
    },
    retryDelay: 1000,
  });

  const healthStatus: HealthStatus = {
    isHealthy: !isError && !!data,
    status: data?.status || 'unknown',
    app_name: data?.app_name,
    version: data?.version,
    responseTime,
    error: error ? String(error) : undefined,
  };

  return {
    healthStatus,
    isLoading,
    isError,
    error,
    refetch,
  };
};

// Hook para testar conectividade geral com AbortController
export const useConnectivityTest = () => {
  const [testResults, setTestResults] = useState<{
    backend: boolean;
    responseTime: number;
    lastTest: Date | null;
  }>({
    backend: false,
    responseTime: 0,
    lastTest: null,
  });
  
  const { createController } = useAbortController();

  const runConnectivityTest = async () => {
    const controller = createController();
    const startTime = Date.now();
    
    try {
      await apiService.get('/health', { signal: controller.signal });
      const responseTime = Date.now() - startTime;
      
      setTestResults({
        backend: true,
        responseTime,
        lastTest: new Date(),
      });
      
      return true;
    } catch (error: any) {
      const responseTime = Date.now() - startTime;
      
      // Não atualizar estado se foi abortado
      if (error.name === 'AbortError') {
        console.log('Connectivity test aborted');
        return false;
      }
      
      setTestResults({
        backend: false,
        responseTime,
        lastTest: new Date(),
      });
      
      console.error('Connectivity test failed:', error);
      return false;
    }
  };

  return {
    testResults,
    runConnectivityTest,
  };
};

// Hook para monitoramento contínuo com cleanup
export const useContinuousHealthMonitor = (intervalMs: number = 60000) => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [healthHistory, setHealthHistory] = useState<HealthStatus[]>([]);
  const { setAbortableInterval, clearAbortableInterval } = useAbortableInterval();
  const { getSignal } = useAbortController();

  const startMonitoring = () => {
    if (isMonitoring) return;
    
    setIsMonitoring(true);
    
    setAbortableInterval(async () => {
      const signal = getSignal();
      const startTime = Date.now();
      
      try {
        const response = await apiService.get('/health', { signal });
        const responseTime = Date.now() - startTime;
        
        const healthStatus: HealthStatus = {
          isHealthy: true,
          status: response.data.status,
          app_name: response.data.app_name,
          version: response.data.version,
          responseTime,
        };
        
        setHealthHistory(prev => [...prev.slice(-19), healthStatus]); // Manter últimos 20
      } catch (error: any) {
        if (error.name === 'AbortError') return;
        
        const responseTime = Date.now() - startTime;
        const healthStatus: HealthStatus = {
          isHealthy: false,
          status: 'error',
          responseTime,
          error: error.message,
        };
        
        setHealthHistory(prev => [...prev.slice(-19), healthStatus]);
      }
    }, intervalMs);
  };

  const stopMonitoring = () => {
    setIsMonitoring(false);
    clearAbortableInterval();
  };

  // Cleanup automático
  useEffect(() => {
    return () => {
      stopMonitoring();
    };
  }, []);

  return {
    isMonitoring,
    healthHistory,
    startMonitoring,
    stopMonitoring,
  };
};
