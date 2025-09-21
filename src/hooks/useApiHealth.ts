/**
 * Hook para verificar saúde da API
 * Testa comunicação frontend-backend
 */

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '@/services/api';

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

  const {
    data,
    error,
    isLoading,
    isError,
    refetch
  } = useQuery({
    queryKey: ['api-health'],
    queryFn: async () => {
      const startTime = Date.now();
      try {
        const response = await apiService.healthCheck();
        const endTime = Date.now();
        setResponseTime(endTime - startTime);
        return response.data;
      } catch (err) {
        const endTime = Date.now();
        setResponseTime(endTime - startTime);
        throw err;
      }
    },
    enabled,
    refetchInterval: 30000, // Refetch a cada 30 segundos
    retry: 3,
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

// Hook para testar conectividade geral
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

  const runConnectivityTest = async () => {
    const startTime = Date.now();
    
    try {
      await apiService.healthCheck();
      const responseTime = Date.now() - startTime;
      
      setTestResults({
        backend: true,
        responseTime,
        lastTest: new Date(),
      });
      
      return true;
    } catch (error) {
      const responseTime = Date.now() - startTime;
      
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
