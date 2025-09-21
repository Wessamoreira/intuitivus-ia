import React, { useEffect, useCallback } from 'react';
import AppLayout from "@/components/layout/AppLayout";
import { 
  OptimizedMetricCard, 
  OptimizedAgentList, 
  OptimizedTaskList 
} from "@/components/optimized/OptimizedComponents";
import { 
  useDashboardStats, 
  useCampaignMetrics, 
  useFilteredAgents, 
  useFilteredTasks, 
  useStoreActions,
  useLoadingState,
  useErrorState 
} from "@/hooks/useOptimizedStore";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Bot, 
  Target, 
  DollarSign, 
  MessageSquare, 
  TrendingUp,
  RefreshCw,
  Search,
  Filter
} from "lucide-react";

const OptimizedDashboard = () => {
  // Hooks otimizados do store
  const dashboardStats = useDashboardStats();
  const campaignMetrics = useCampaignMetrics();
  const filteredAgents = useFilteredAgents();
  const filteredTasks = useFilteredTasks();
  
  // Estados de loading e erro
  const { dashboard: isDashboardLoading } = useLoadingState(['dashboard']);
  const { dashboard: dashboardError } = useErrorState(['dashboard']);
  
  // Ações do store
  const {
    setLoading,
    setError,
    updateAgent,
    updateTask,
    addNotification,
    updateMetrics
  } = useStoreActions();

  // Simular carregamento de dados (substituir por API real)
  const loadDashboardData = useCallback(async () => {
    setLoading('dashboard', true);
    setError('dashboard', undefined);
    
    try {
      // Simular delay de API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Atualizar métricas em tempo real
      updateMetrics({
        activeAgents: dashboardStats.activeAgents,
        runningTasks: dashboardStats.runningTasks,
        todayTasks: dashboardStats.todayTasks,
        todayRevenue: campaignMetrics.totalSpent,
      });
      
    } catch (error) {
      setError('dashboard', 'Failed to load dashboard data');
      addNotification({
        type: 'error',
        title: 'Dashboard Error',
        message: 'Failed to load dashboard data. Please try again.',
      });
    } finally {
      setLoading('dashboard', false);
    }
  }, [
    setLoading, 
    setError, 
    updateMetrics, 
    addNotification,
    dashboardStats.activeAgents,
    dashboardStats.runningTasks,
    dashboardStats.todayTasks,
    campaignMetrics.totalSpent
  ]);

  // Carregar dados na inicialização
  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Auto-refresh a cada 30 segundos
  useEffect(() => {
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, [loadDashboardData]);

  // Handlers otimizados
  const handleAgentStatusChange = useCallback((agentId: string, status: 'active' | 'paused' | 'inactive' | 'error') => {
    updateAgent(agentId, { 
      status,
      lastActivity: new Date().toISOString()
    });
    
    addNotification({
      type: 'info',
      title: 'Agent Status Updated',
      message: `Agent status changed to ${status}`,
    });
  }, [updateAgent, addNotification]);

  const handleTaskRetry = useCallback((taskId: string) => {
    updateTask(taskId, { 
      status: 'pending',
      error: undefined,
      updatedAt: new Date().toISOString()
    });
    
    addNotification({
      type: 'info',
      title: 'Task Retried',
      message: 'Task has been queued for retry',
    });
  }, [updateTask, addNotification]);

  const handleTaskCancel = useCallback((taskId: string) => {
    updateTask(taskId, { 
      status: 'cancelled',
      updatedAt: new Date().toISOString()
    });
    
    addNotification({
      type: 'warning',
      title: 'Task Cancelled',
      message: 'Task has been cancelled',
    });
  }, [updateTask, addNotification]);

  const handleRefresh = useCallback(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  if (dashboardError) {
    return (
      <AppLayout>
        <div className="flex-1 flex items-center justify-center p-8">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="text-red-600">Dashboard Error</CardTitle>
              <CardDescription>{dashboardError}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={handleRefresh} className="w-full">
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="flex-1 space-y-6 p-4 md:p-8 pt-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
            <p className="text-muted-foreground">
              Monitor and manage your AI agent fleet
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleRefresh}
              disabled={isDashboardLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isDashboardLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Métricas principais */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <OptimizedMetricCard
            title="Total Agents"
            value={dashboardStats.totalAgents}
            description={`${dashboardStats.activeAgents} active`}
            trend={dashboardStats.activeAgents > 0 ? 15.2 : undefined}
            icon={<Bot className="h-4 w-4" />}
            loading={isDashboardLoading}
          />
          
          <OptimizedMetricCard
            title="Tasks Today"
            value={dashboardStats.todayTasks}
            description={`${dashboardStats.completedToday} completed`}
            trend={dashboardStats.successRate}
            icon={<Target className="h-4 w-4" />}
            loading={isDashboardLoading}
          />
          
          <OptimizedMetricCard
            title="Revenue Today"
            value={`$${campaignMetrics.totalSpent.toLocaleString()}`}
            description={`${campaignMetrics.activeCampaigns} campaigns`}
            trend={12.5}
            icon={<DollarSign className="h-4 w-4" />}
            loading={isDashboardLoading}
          />
          
          <OptimizedMetricCard
            title="Success Rate"
            value={`${dashboardStats.successRate.toFixed(1)}%`}
            description="Today's performance"
            trend={dashboardStats.successRate - 85}
            icon={<TrendingUp className="h-4 w-4" />}
            loading={isDashboardLoading}
          />
        </div>

        {/* Conteúdo principal */}
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="agents">
              Agents
              <Badge variant="secondary" className="ml-2">
                {filteredAgents.length}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="tasks">
              Tasks
              <Badge variant="secondary" className="ml-2">
                {filteredTasks.tasks.length}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {/* Agentes ativos */}
              <Card>
                <CardHeader>
                  <CardTitle>Active Agents</CardTitle>
                  <CardDescription>
                    Currently running AI agents
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <OptimizedAgentList
                    agents={filteredAgents.slice(0, 3)}
                    onStatusChange={handleAgentStatusChange}
                  />
                  {filteredAgents.length > 3 && (
                    <div className="mt-4 text-center">
                      <Button variant="ghost" size="sm">
                        View all {filteredAgents.length} agents
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Tasks recentes */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Tasks</CardTitle>
                  <CardDescription>
                    Latest task executions
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <OptimizedTaskList
                    tasks={filteredTasks.tasks.slice(0, 5)}
                    agents={filteredAgents}
                    onRetry={handleTaskRetry}
                    onCancel={handleTaskCancel}
                  />
                  {filteredTasks.total > 5 && (
                    <div className="mt-4 text-center">
                      <Button variant="ghost" size="sm">
                        View all {filteredTasks.total} tasks
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Métricas de campanha */}
            <Card>
              <CardHeader>
                <CardTitle>Campaign Performance</CardTitle>
                <CardDescription>
                  Active advertising campaigns overview
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      ${campaignMetrics.totalBudget.toLocaleString()}
                    </div>
                    <div className="text-sm text-muted-foreground">Total Budget</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {campaignMetrics.avgCTR.toFixed(2)}%
                    </div>
                    <div className="text-sm text-muted-foreground">Avg CTR</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {campaignMetrics.avgCVR.toFixed(2)}%
                    </div>
                    <div className="text-sm text-muted-foreground">Avg CVR</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {campaignMetrics.budgetUtilization.toFixed(1)}%
                    </div>
                    <div className="text-sm text-muted-foreground">Budget Used</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="agents" className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Search agents..." className="pl-8" />
              </div>
              <Button variant="outline" size="sm">
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </Button>
            </div>
            
            <OptimizedAgentList
              agents={filteredAgents}
              onStatusChange={handleAgentStatusChange}
            />
          </TabsContent>

          <TabsContent value="tasks" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="Search tasks..." className="pl-8" />
                </div>
                <Button variant="outline" size="sm">
                  <Filter className="h-4 w-4 mr-2" />
                  Filter
                </Button>
              </div>
              
              <div className="text-sm text-muted-foreground">
                Showing {filteredTasks.tasks.length} of {filteredTasks.total} tasks
              </div>
            </div>
            
            <OptimizedTaskList
              tasks={filteredTasks.tasks}
              agents={filteredAgents}
              onRetry={handleTaskRetry}
              onCancel={handleTaskCancel}
            />
          </TabsContent>

          <TabsContent value="campaigns" className="space-y-4">
            <div className="text-center py-8">
              <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium">Campaign Management</h3>
              <p className="text-muted-foreground">
                Campaign management interface will be implemented here
              </p>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
};

export default OptimizedDashboard;
