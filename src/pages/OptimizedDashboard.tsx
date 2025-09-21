/**
 * Optimized Dashboard Page
 * Dashboard otimizado com todos os componentes e hooks otimizados
 */

import React, { memo, useCallback, useMemo, Suspense } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Bot, 
  CheckCircle, 
  Clock, 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Activity,
  Plus,
  RefreshCw,
  Settings
} from 'lucide-react';

// Componentes otimizados
import { OptimizedAgentCard } from '@/components/optimized/OptimizedAgentCard';
import { OptimizedTaskList } from '@/components/optimized/OptimizedTaskList';

// Hooks otimizados
import { useOptimizedAgents, useOptimizedTasks, useOptimizedDashboardStats } from '@/hooks/useOptimizedData';
import { useComputedStats, useRecentNotifications } from '@/stores/useAppStore';
import { useUserProfile, useUserPermissions } from '@/stores/useAuthStore';
import { toast } from '@/hooks/use-toast';

// Componente de estatística memoizado
const StatCard = memo<{
  title: string;
  value: string | number;
  description?: string;
  icon: React.ComponentType<any>;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
}>(({ title, value, description, icon: Icon, trend, trendValue }) => {
  const trendConfig = useMemo(() => {
    switch (trend) {
      case 'up':
        return { icon: TrendingUp, color: 'text-green-600', bgColor: 'bg-green-50' };
      case 'down':
        return { icon: TrendingDown, color: 'text-red-600', bgColor: 'bg-red-50' };
      default:
        return { icon: Activity, color: 'text-gray-600', bgColor: 'bg-gray-50' };
    }
  }, [trend]);

  const TrendIcon = trendConfig.icon;

  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className={`p-2 rounded-full ${trendConfig.bgColor}`}>
          <Icon className={`h-4 w-4 ${trendConfig.color}`} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">
            {description}
          </p>
        )}
        {trend && trendValue && (
          <div className="flex items-center mt-2">
            <TrendIcon className={`h-3 w-3 mr-1 ${trendConfig.color}`} />
            <span className={`text-xs ${trendConfig.color}`}>
              {trendValue}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
});

StatCard.displayName = 'StatCard';

// Componente de loading para seções
const SectionSkeleton = memo(() => (
  <Card>
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
));

SectionSkeleton.displayName = 'SectionSkeleton';

// Componente principal do dashboard
export const OptimizedDashboard = memo(() => {
  const userProfile = useUserProfile();
  const userPermissions = useUserPermissions();
  
  // Hooks de dados otimizados
  const { stats: dashboardStats, isLoading: statsLoading, refetch: refetchStats } = useOptimizedDashboardStats();
  const { 
    agents, 
    isLoading: agentsLoading, 
    createAgent, 
    updateAgentStatus,
    isCreating: isCreatingAgent,
    refetch: refetchAgents
  } = useOptimizedAgents();
  
  const { 
    tasks, 
    isLoading: tasksLoading, 
    updateTaskStatus,
    refetch: refetchTasks
  } = useOptimizedTasks();

  // Dados computados do store
  const computedStats = useComputedStats();
  const recentNotifications = useRecentNotifications(3);

  // Callbacks memoizados
  const handleAgentStatusChange = useCallback((agentId: string, newStatus: string) => {
    updateAgentStatus({ agentId, status: newStatus });
  }, [updateAgentStatus]);

  const handleTaskStatusChange = useCallback((taskId: string, newStatus: string) => {
    updateTaskStatus({ taskId, status: newStatus });
  }, [updateTaskStatus]);

  const handleCreateAgent = useCallback(() => {
    if (!userPermissions.canCreateAgents) {
      toast({
        title: "Permissão Negada",
        description: "Você precisa de uma assinatura premium para criar agentes.",
        variant: "destructive",
      });
      return;
    }

    // Aqui você abriria um modal ou navegaria para página de criação
    toast({
      title: "Criar Agente",
      description: "Funcionalidade em desenvolvimento.",
    });
  }, [userPermissions.canCreateAgents]);

  const handleAgentEdit = useCallback((agentId: string) => {
    toast({
      title: "Editar Agente",
      description: `Editando agente ${agentId}`,
    });
  }, []);

  const handleAgentViewDetails = useCallback((agentId: string) => {
    toast({
      title: "Detalhes do Agente",
      description: `Visualizando detalhes do agente ${agentId}`,
    });
  }, []);

  const handleTaskClick = useCallback((taskId: string) => {
    toast({
      title: "Detalhes da Tarefa",
      description: `Visualizando tarefa ${taskId}`,
    });
  }, []);

  const handleRefreshAll = useCallback(() => {
    Promise.all([
      refetchStats(),
      refetchAgents(),
      refetchTasks()
    ]).then(() => {
      toast({
        title: "Dados Atualizados",
        description: "Todos os dados foram atualizados com sucesso.",
      });
    });
  }, [refetchStats, refetchAgents, refetchTasks]);

  // Filtrar agentes ativos para exibição
  const activeAgents = useMemo(() => {
    return agents.filter(agent => agent.status === 'active').slice(0, 6);
  }, [agents]);

  // Tarefas recentes
  const recentTasks = useMemo(() => {
    return tasks
      .sort((a, b) => new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime())
      .slice(0, 10);
  }, [tasks]);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">
                Bem-vindo, {userProfile?.firstName || 'Usuário'}!
              </h1>
              <p className="text-muted-foreground">
                Gerencie seus agentes de IA e acompanhe o desempenho
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <Badge variant="outline" className="flex items-center space-x-1">
                <Users className="h-3 w-3" />
                <span>{userProfile?.subscriptionType || 'Free'}</span>
              </Badge>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefreshAll}
                disabled={statsLoading || agentsLoading || tasksLoading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${(statsLoading || agentsLoading || tasksLoading) ? 'animate-spin' : ''}`} />
                Atualizar
              </Button>
              
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Configurações
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-6 space-y-6">
        {/* Estatísticas Principais */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {statsLoading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16" />
                  <Skeleton className="h-3 w-32 mt-2" />
                </CardContent>
              </Card>
            ))
          ) : (
            <>
              <StatCard
                title="Total de Agentes"
                value={computedStats?.totalAgents || 0}
                description={`${computedStats?.activeAgents || 0} ativos`}
                icon={Bot}
                trend={dashboardStats?.growthTrend}
                trendValue={dashboardStats?.monthlyGrowth ? `${dashboardStats.monthlyGrowth}%` : undefined}
              />
              
              <StatCard
                title="Tarefas Concluídas"
                value={computedStats?.completedTasks || 0}
                description={`de ${computedStats?.totalTasks || 0} total`}
                icon={CheckCircle}
                trend="up"
                trendValue={`${dashboardStats?.completionRate || 0}%`}
              />
              
              <StatCard
                title="Taxa de Sucesso"
                value={`${dashboardStats?.completionRate || 0}%`}
                description="Últimos 30 dias"
                icon={TrendingUp}
                trend={dashboardStats?.completionRate && dashboardStats.completionRate > 80 ? 'up' : 'stable'}
              />
              
              <StatCard
                title="Receita Total"
                value={`R$ ${dashboardStats?.totalRevenue?.toLocaleString() || '0'}`}
                description="Este mês"
                icon={Activity}
                trend={dashboardStats?.monthlyGrowth && dashboardStats.monthlyGrowth > 0 ? 'up' : 'stable'}
                trendValue={dashboardStats?.monthlyGrowth ? `${dashboardStats.monthlyGrowth}%` : undefined}
              />
            </>
          )}
        </div>

        {/* Seção de Agentes */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center space-x-2">
                  <Bot className="h-5 w-5" />
                  <span>Agentes Ativos</span>
                  <Badge variant="secondary">{activeAgents.length}</Badge>
                </CardTitle>
                <CardDescription>
                  Gerencie e monitore seus agentes de IA
                </CardDescription>
              </div>
              
              <Button 
                onClick={handleCreateAgent}
                disabled={!userPermissions.canCreateAgents || isCreatingAgent}
                className="flex items-center space-x-2"
              >
                <Plus className="h-4 w-4" />
                <span>Novo Agente</span>
              </Button>
            </div>
          </CardHeader>
          
          <CardContent>
            {agentsLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Array.from({ length: 6 }).map((_, i) => (
                  <SectionSkeleton key={i} />
                ))}
              </div>
            ) : activeAgents.length === 0 ? (
              <div className="text-center py-8">
                <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">
                  Nenhum agente ativo encontrado.
                </p>
                <Button 
                  onClick={handleCreateAgent}
                  className="mt-4"
                  disabled={!userPermissions.canCreateAgents}
                >
                  Criar Primeiro Agente
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {activeAgents.map((agent) => (
                  <OptimizedAgentCard
                    key={agent.id}
                    agent={agent}
                    onStatusChange={handleAgentStatusChange}
                    onEdit={handleAgentEdit}
                    onViewDetails={handleAgentViewDetails}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Seção de Tarefas */}
        <Suspense fallback={<SectionSkeleton />}>
          <OptimizedTaskList
            onTaskClick={handleTaskClick}
            onStatusChange={handleTaskStatusChange}
          />
        </Suspense>

        {/* Notificações Recentes */}
        {recentNotifications.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5" />
                <span>Atividade Recente</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentNotifications.map((notification) => (
                  <div key={notification.id} className="flex items-center space-x-3 p-3 rounded-lg bg-muted/50">
                    <div className="flex-1">
                      <p className="text-sm font-medium">{notification.title}</p>
                      <p className="text-xs text-muted-foreground">{notification.message}</p>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      <Clock className="h-3 w-3 inline mr-1" />
                      {new Date(notification.createdAt).toLocaleTimeString()}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
});

OptimizedDashboard.displayName = 'OptimizedDashboard';

export default OptimizedDashboard;
