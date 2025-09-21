/**
 * Lazy Components
 * Sistema de lazy loading para componentes pesados
 */

import { lazy, Suspense, ComponentType, useState, useEffect } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

// Componente de loading genérico
export const ComponentSkeleton = ({ className = "" }: { className?: string }) => (
  <Card className={className}>
    <CardHeader>
      <Skeleton className="h-6 w-32" />
      <Skeleton className="h-4 w-48" />
    </CardHeader>
    <CardContent className="space-y-3">
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
    </CardContent>
  </Card>
);

// Loading para gráficos
export const ChartSkeleton = () => (
  <Card>
    <CardHeader>
      <Skeleton className="h-6 w-40" />
    </CardHeader>
    <CardContent>
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center space-x-2">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-3 flex-1" />
            <Skeleton className="h-3 w-12" />
          </div>
        ))}
      </div>
    </CardContent>
  </Card>
);

// Loading para tabelas
export const TableSkeleton = () => (
  <Card>
    <CardHeader>
      <Skeleton className="h-6 w-32" />
    </CardHeader>
    <CardContent>
      <div className="space-y-3">
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-full" />
          ))}
        </div>
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="grid grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, j) => (
              <Skeleton key={j} className="h-3 w-full" />
            ))}
          </div>
        ))}
      </div>
    </CardContent>
  </Card>
);

// Loading centralizado com spinner
export const CenteredLoader = ({ message = "Carregando..." }: { message?: string }) => (
  <div className="flex flex-col items-center justify-center p-8 space-y-4">
    <Loader2 className="h-8 w-8 animate-spin text-primary" />
    <p className="text-sm text-muted-foreground">{message}</p>
  </div>
);

// HOC para lazy loading com fallback customizado
export const withLazyLoading = <P extends object>(
  Component: ComponentType<P>,
  fallback: React.ComponentType = ComponentSkeleton
) => {
  const LazyComponent = lazy(() => Promise.resolve({ default: Component }));
  
  return (props: P) => (
    <Suspense fallback={<fallback />}>
      <LazyComponent {...props} />
    </Suspense>
  );
};

// Componentes lazy carregados dinamicamente
export const LazyAnalyticsChart = lazy(() => 
  import('@/components/charts/AnalyticsChart').then(module => ({
    default: module.AnalyticsChart
  }))
);

export const LazyAgentPerformanceChart = lazy(() => 
  import('@/components/charts/AgentPerformanceChart').then(module => ({
    default: module.AgentPerformanceChart
  }))
);

export const LazyTasksTable = lazy(() => 
  import('@/components/tables/TasksTable').then(module => ({
    default: module.TasksTable
  }))
);

export const LazyAgentsGrid = lazy(() => 
  import('@/components/grids/AgentsGrid').then(module => ({
    default: module.AgentsGrid
  }))
);

export const LazyCampaignsManager = lazy(() => 
  import('@/components/campaigns/CampaignsManager').then(module => ({
    default: module.CampaignsManager
  }))
);

// Componentes com fallbacks específicos
export const AnalyticsChartWithLoading = (props: any) => (
  <Suspense fallback={<ChartSkeleton />}>
    <LazyAnalyticsChart {...props} />
  </Suspense>
);

export const AgentPerformanceChartWithLoading = (props: any) => (
  <Suspense fallback={<ChartSkeleton />}>
    <LazyAgentPerformanceChart {...props} />
  </Suspense>
);

export const TasksTableWithLoading = (props: any) => (
  <Suspense fallback={<TableSkeleton />}>
    <LazyTasksTable {...props} />
  </Suspense>
);

export const AgentsGridWithLoading = (props: any) => (
  <Suspense fallback={
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <ComponentSkeleton key={i} />
      ))}
    </div>
  }>
    <LazyAgentsGrid {...props} />
  </Suspense>
);

export const CampaignsManagerWithLoading = (props: any) => (
  <Suspense fallback={<CenteredLoader message="Carregando campanhas..." />}>
    <LazyCampaignsManager {...props} />
  </Suspense>
);

// Hook para lazy loading condicional
export const useLazyComponent = (shouldLoad: boolean, importFn: () => Promise<any>) => {
  const [Component, setComponent] = useState<ComponentType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (shouldLoad && !Component && !isLoading) {
      setIsLoading(true);
      setError(null);
      
      importFn()
        .then((module) => {
          setComponent(() => module.default || module);
        })
        .catch((err) => {
          setError(err);
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [shouldLoad, Component, isLoading, importFn]);

  return { Component, isLoading, error };
};
