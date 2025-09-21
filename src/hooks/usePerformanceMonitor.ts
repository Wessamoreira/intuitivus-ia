/**
 * Performance Monitor Hook
 * Hook para monitorar performance da aplicação React
 */

import { useEffect, useCallback, useState, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';

interface PerformanceMetrics {
  // Core Web Vitals
  fcp?: number; // First Contentful Paint
  lcp?: number; // Largest Contentful Paint
  fid?: number; // First Input Delay
  cls?: number; // Cumulative Layout Shift
  
  // Métricas customizadas
  componentRenderTime: number;
  apiResponseTime: number;
  memoryUsage?: number;
  bundleSize?: number;
  
  // Métricas de rede
  connectionType?: string;
  effectiveType?: string;
  
  // Timestamps
  timestamp: number;
}

interface ComponentPerformance {
  componentName: string;
  renderCount: number;
  averageRenderTime: number;
  lastRenderTime: number;
  totalRenderTime: number;
}

export const usePerformanceMonitor = (componentName?: string) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>([]);
  const [componentMetrics, setComponentMetrics] = useState<Map<string, ComponentPerformance>>(new Map());
  const renderStartTime = useRef<number>(0);
  const observerRef = useRef<PerformanceObserver | null>(null);

  // Monitorar Core Web Vitals
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const metric: Partial<PerformanceMetrics> = {
          timestamp: Date.now(),
          componentRenderTime: 0,
          apiResponseTime: 0,
        };

        switch (entry.entryType) {
          case 'paint':
            if (entry.name === 'first-contentful-paint') {
              metric.fcp = entry.startTime;
            }
            break;
            
          case 'largest-contentful-paint':
            metric.lcp = entry.startTime;
            break;
            
          case 'first-input':
            metric.fid = (entry as any).processingStart - entry.startTime;
            break;
            
          case 'layout-shift':
            if (!(entry as any).hadRecentInput) {
              metric.cls = (metric.cls || 0) + (entry as any).value;
            }
            break;
        }

        setMetrics(prev => [...prev.slice(-49), metric as PerformanceMetrics]);
      }
    });

    // Observar diferentes tipos de métricas
    try {
      observer.observe({ entryTypes: ['paint', 'largest-contentful-paint', 'first-input', 'layout-shift'] });
      observerRef.current = observer;
    } catch (error) {
      console.warn('Performance Observer not supported:', error);
    }

    return () => {
      observer.disconnect();
    };
  }, []);

  // Monitorar renderização de componentes
  useEffect(() => {
    if (componentName) {
      renderStartTime.current = performance.now();
    }
  });

  useEffect(() => {
    if (componentName && renderStartTime.current > 0) {
      const renderTime = performance.now() - renderStartTime.current;
      
      setComponentMetrics(prev => {
        const existing = prev.get(componentName) || {
          componentName,
          renderCount: 0,
          averageRenderTime: 0,
          lastRenderTime: 0,
          totalRenderTime: 0,
        };

        const newCount = existing.renderCount + 1;
        const newTotal = existing.totalRenderTime + renderTime;
        
        const updated: ComponentPerformance = {
          ...existing,
          renderCount: newCount,
          lastRenderTime: renderTime,
          totalRenderTime: newTotal,
          averageRenderTime: newTotal / newCount,
        };

        const newMap = new Map(prev);
        newMap.set(componentName, updated);
        return newMap;
      });

      renderStartTime.current = 0;
    }
  });

  // Monitorar uso de memória
  const getMemoryUsage = useCallback(() => {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit,
      };
    }
    return null;
  }, []);

  // Monitorar conexão de rede
  const getNetworkInfo = useCallback(() => {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      return {
        effectiveType: connection.effectiveType,
        downlink: connection.downlink,
        rtt: connection.rtt,
        saveData: connection.saveData,
      };
    }
    return null;
  }, []);

  // Medir tempo de resposta da API
  const measureApiCall = useCallback(async <T>(
    apiCall: () => Promise<T>,
    endpoint?: string
  ): Promise<{ data: T; responseTime: number }> => {
    const startTime = performance.now();
    
    try {
      const data = await apiCall();
      const responseTime = performance.now() - startTime;
      
      // Registrar métrica
      setMetrics(prev => [...prev.slice(-49), {
        timestamp: Date.now(),
        componentRenderTime: 0,
        apiResponseTime: responseTime,
      }]);

      // Log para debugging
      if (endpoint) {
        console.log(`API ${endpoint}: ${responseTime.toFixed(2)}ms`);
      }

      return { data, responseTime };
    } catch (error) {
      const responseTime = performance.now() - startTime;
      console.error(`API Error after ${responseTime.toFixed(2)}ms:`, error);
      throw error;
    }
  }, []);

  // Obter estatísticas de performance
  const getPerformanceStats = useCallback(() => {
    const recentMetrics = metrics.slice(-20);
    
    if (recentMetrics.length === 0) {
      return null;
    }

    const apiTimes = recentMetrics
      .map(m => m.apiResponseTime)
      .filter(t => t > 0);
    
    const renderTimes = Array.from(componentMetrics.values())
      .map(c => c.averageRenderTime);

    return {
      // API Performance
      averageApiTime: apiTimes.length > 0 ? apiTimes.reduce((a, b) => a + b, 0) / apiTimes.length : 0,
      maxApiTime: apiTimes.length > 0 ? Math.max(...apiTimes) : 0,
      minApiTime: apiTimes.length > 0 ? Math.min(...apiTimes) : 0,
      
      // Render Performance
      averageRenderTime: renderTimes.length > 0 ? renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length : 0,
      maxRenderTime: renderTimes.length > 0 ? Math.max(...renderTimes) : 0,
      
      // Core Web Vitals
      latestFCP: recentMetrics.find(m => m.fcp)?.fcp,
      latestLCP: recentMetrics.find(m => m.lcp)?.lcp,
      latestFID: recentMetrics.find(m => m.fid)?.fid,
      latestCLS: recentMetrics.find(m => m.cls)?.cls,
      
      // Memory
      memoryUsage: getMemoryUsage(),
      
      // Network
      networkInfo: getNetworkInfo(),
      
      // Component stats
      componentCount: componentMetrics.size,
      totalRenders: Array.from(componentMetrics.values()).reduce((sum, c) => sum + c.renderCount, 0),
    };
  }, [metrics, componentMetrics, getMemoryUsage, getNetworkInfo]);

  // Detectar performance issues
  const getPerformanceIssues = useCallback(() => {
    const stats = getPerformanceStats();
    const issues: string[] = [];

    if (!stats) return issues;

    // API muito lenta
    if (stats.averageApiTime > 2000) {
      issues.push(`API response time is slow: ${stats.averageApiTime.toFixed(0)}ms average`);
    }

    // Renderização lenta
    if (stats.averageRenderTime > 16) {
      issues.push(`Component rendering is slow: ${stats.averageRenderTime.toFixed(2)}ms average`);
    }

    // Core Web Vitals issues
    if (stats.latestLCP && stats.latestLCP > 2500) {
      issues.push(`LCP is poor: ${stats.latestLCP.toFixed(0)}ms`);
    }

    if (stats.latestFID && stats.latestFID > 100) {
      issues.push(`FID is poor: ${stats.latestFID.toFixed(0)}ms`);
    }

    if (stats.latestCLS && stats.latestCLS > 0.1) {
      issues.push(`CLS is poor: ${stats.latestCLS.toFixed(3)}`);
    }

    // Memory issues
    if (stats.memoryUsage) {
      const usagePercent = (stats.memoryUsage.used / stats.memoryUsage.limit) * 100;
      if (usagePercent > 80) {
        issues.push(`High memory usage: ${usagePercent.toFixed(1)}%`);
      }
    }

    return issues;
  }, [getPerformanceStats]);

  // Enviar métricas para backend
  const reportMetrics = useCallback(async () => {
    const stats = getPerformanceStats();
    if (!stats) return;

    try {
      await fetch('/api/v1/metrics/performance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...stats,
          userAgent: navigator.userAgent,
          url: window.location.href,
          timestamp: Date.now(),
        }),
      });
    } catch (error) {
      console.warn('Failed to report performance metrics:', error);
    }
  }, [getPerformanceStats]);

  // Auto-report a cada 5 minutos
  useEffect(() => {
    const interval = setInterval(reportMetrics, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [reportMetrics]);

  return {
    metrics,
    componentMetrics: Array.from(componentMetrics.values()),
    measureApiCall,
    getPerformanceStats,
    getPerformanceIssues,
    reportMetrics,
  };
};

// Hook para monitorar performance de queries React Query
export const useQueryPerformanceMonitor = () => {
  const { measureApiCall } = usePerformanceMonitor();

  const createMonitoredQuery = useCallback((
    queryKey: any[],
    queryFn: () => Promise<any>,
    options: any = {}
  ) => {
    return useQuery({
      queryKey,
      queryFn: () => measureApiCall(queryFn, queryKey.join('/')).then(result => result.data),
      ...options,
    });
  }, [measureApiCall]);

  return { createMonitoredQuery };
};

// HOC para monitorar performance de componentes
export const withPerformanceMonitoring = <P extends object>(
  Component: React.ComponentType<P>,
  componentName?: string
) => {
  const MonitoredComponent = (props: P) => {
    const name = componentName || Component.displayName || Component.name || 'Unknown';
    usePerformanceMonitor(name);
    
    return <Component {...props} />;
  };

  MonitoredComponent.displayName = `withPerformanceMonitoring(${Component.displayName || Component.name})`;
  
  return MonitoredComponent;
};
