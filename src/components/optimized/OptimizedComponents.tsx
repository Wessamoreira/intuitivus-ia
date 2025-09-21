import React, { memo, useMemo, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Bot, 
  Activity, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  XCircle,
  PlayCircle,
  PauseCircle 
} from 'lucide-react';
import type { Agent, Task, Campaign } from '@/stores/types';

// Props interfaces para type safety
interface AgentCardProps {
  agent: Agent;
  onStatusChange?: (agentId: string, status: Agent['status']) => void;
  onEdit?: (agentId: string) => void;
  className?: string;
}

interface TaskItemProps {
  task: Task;
  agentName?: string;
  onRetry?: (taskId: string) => void;
  onCancel?: (taskId: string) => void;
  className?: string;
}

interface CampaignCardProps {
  campaign: Campaign;
  onPause?: (campaignId: string) => void;
  onResume?: (campaignId: string) => void;
  onEdit?: (campaignId: string) => void;
  className?: string;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
  trend?: number;
  icon?: React.ReactNode;
  loading?: boolean;
  className?: string;
}

// Componente de Agent otimizado
export const OptimizedAgentCard = memo<AgentCardProps>(({ 
  agent, 
  onStatusChange, 
  onEdit, 
  className 
}) => {
  // Memoizar cálculos
  const statusColor = useMemo(() => {
    switch (agent.status) {
      case 'active': return 'bg-green-500';
      case 'paused': return 'bg-yellow-500';
      case 'inactive': return 'bg-gray-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  }, [agent.status]);

  const statusVariant = useMemo(() => {
    switch (agent.status) {
      case 'active': return 'default';
      case 'paused': return 'secondary';
      case 'inactive': return 'outline';
      case 'error': return 'destructive';
      default: return 'outline';
    }
  }, [agent.status]);

  // Callbacks memoizados
  const handleStatusToggle = useCallback(() => {
    if (!onStatusChange) return;
    
    const newStatus = agent.status === 'active' ? 'paused' : 'active';
    onStatusChange(agent.id, newStatus);
  }, [agent.id, agent.status, onStatusChange]);

  const handleEdit = useCallback(() => {
    onEdit?.(agent.id);
  }, [agent.id, onEdit]);

  return (
    <Card className={`hover:shadow-lg transition-shadow ${className}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-2">
          <div className="relative">
            <div className="h-10 w-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm">
              {agent.name.charAt(0).toUpperCase()}
            </div>
            <div className={`absolute -bottom-1 -right-1 h-3 w-3 rounded-full border-2 border-background ${statusColor}`}></div>
          </div>
          <div>
            <CardTitle className="text-sm font-medium">{agent.name}</CardTitle>
            <CardDescription className="text-xs">{agent.type}</CardDescription>
          </div>
        </div>
        <Badge variant={statusVariant} className="text-xs">
          {agent.status}
        </Badge>
      </CardHeader>
      
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Performance</span>
          <span className="font-medium">{agent.successRate}%</span>
        </div>
        <Progress value={agent.successRate} className="h-1" />
        
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{agent.tasksCompleted} tasks completed</span>
          <span>{agent.lastActivity}</span>
        </div>
        
        <div className="flex space-x-2 pt-2">
          <Button 
            size="sm" 
            variant="ghost" 
            onClick={handleStatusToggle}
            className="flex-1"
          >
            {agent.status === 'active' ? (
              <PauseCircle className="h-4 w-4 mr-1" />
            ) : (
              <PlayCircle className="h-4 w-4 mr-1" />
            )}
            {agent.status === 'active' ? 'Pause' : 'Start'}
          </Button>
          <Button 
            size="sm" 
            variant="outline" 
            onClick={handleEdit}
          >
            Edit
          </Button>
        </div>
      </CardContent>
    </Card>
  );
});

OptimizedAgentCard.displayName = 'OptimizedAgentCard';

// Componente de Task otimizado
export const OptimizedTaskItem = memo<TaskItemProps>(({ 
  task, 
  agentName, 
  onRetry, 
  onCancel, 
  className 
}) => {
  // Memoizar ícone do status
  const statusIcon = useMemo(() => {
    switch (task.status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  }, [task.status]);

  const statusColor = useMemo(() => {
    switch (task.status) {
      case 'completed': return 'text-green-600 bg-green-50';
      case 'failed': return 'text-red-600 bg-red-50';
      case 'running': return 'text-blue-600 bg-blue-50';
      case 'pending': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  }, [task.status]);

  // Callbacks memoizados
  const handleRetry = useCallback(() => {
    onRetry?.(task.id);
  }, [task.id, onRetry]);

  const handleCancel = useCallback(() => {
    onCancel?.(task.id);
  }, [task.id, onCancel]);

  return (
    <div className={`flex items-center space-x-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors ${className}`}>
      <div className="flex-shrink-0">
        {statusIcon}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium truncate">
            {task.type}
          </p>
          <Badge className={`text-xs ${statusColor}`}>
            {task.status}
          </Badge>
        </div>
        
        <div className="flex items-center justify-between text-xs text-muted-foreground mt-1">
          <span>{agentName || 'Unknown Agent'}</span>
          <span>{new Date(task.createdAt).toLocaleTimeString()}</span>
        </div>
        
        {task.executionTime && (
          <div className="text-xs text-muted-foreground mt-1">
            Execution time: {task.executionTime}ms
          </div>
        )}
        
        {task.error && (
          <div className="text-xs text-red-600 mt-1 truncate">
            Error: {task.error}
          </div>
        )}
      </div>
      
      {(task.status === 'failed' || task.status === 'running') && (
        <div className="flex space-x-1">
          {task.status === 'failed' && (
            <Button size="sm" variant="ghost" onClick={handleRetry}>
              Retry
            </Button>
          )}
          {task.status === 'running' && (
            <Button size="sm" variant="ghost" onClick={handleCancel}>
              Cancel
            </Button>
          )}
        </div>
      )}
    </div>
  );
});

OptimizedTaskItem.displayName = 'OptimizedTaskItem';

// Componente de Campaign otimizado
export const OptimizedCampaignCard = memo<CampaignCardProps>(({ 
  campaign, 
  onPause, 
  onResume, 
  onEdit, 
  className 
}) => {
  // Memoizar cálculos de métricas
  const metrics = useMemo(() => {
    const ctr = campaign.impressions > 0 
      ? (campaign.clicks / campaign.impressions) * 100 
      : 0;
    const cvr = campaign.clicks > 0 
      ? (campaign.conversions / campaign.clicks) * 100 
      : 0;
    const budgetUsed = campaign.budget > 0 
      ? (campaign.spent / campaign.budget) * 100 
      : 0;

    return { ctr, cvr, budgetUsed };
  }, [campaign.impressions, campaign.clicks, campaign.conversions, campaign.budget, campaign.spent]);

  const platformColor = useMemo(() => {
    switch (campaign.platform) {
      case 'google_ads': return 'bg-blue-500';
      case 'meta_ads': return 'bg-blue-600';
      case 'tiktok_ads': return 'bg-black';
      default: return 'bg-gray-500';
    }
  }, [campaign.platform]);

  // Callbacks memoizados
  const handleToggle = useCallback(() => {
    if (campaign.status === 'active') {
      onPause?.(campaign.id);
    } else {
      onResume?.(campaign.id);
    }
  }, [campaign.id, campaign.status, onPause, onResume]);

  const handleEdit = useCallback(() => {
    onEdit?.(campaign.id);
  }, [campaign.id, onEdit]);

  return (
    <Card className={`hover:shadow-lg transition-shadow ${className}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-2">
          <div className={`h-3 w-3 rounded-full ${platformColor}`}></div>
          <CardTitle className="text-sm font-medium">{campaign.name}</CardTitle>
        </div>
        <Badge variant={campaign.status === 'active' ? 'default' : 'secondary'}>
          {campaign.status}
        </Badge>
      </CardHeader>
      
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Budget</span>
            <div className="font-medium">${campaign.budget.toLocaleString()}</div>
          </div>
          <div>
            <span className="text-muted-foreground">Spent</span>
            <div className="font-medium">${campaign.spent.toLocaleString()}</div>
          </div>
        </div>
        
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span>Budget Usage</span>
            <span>{metrics.budgetUsed.toFixed(1)}%</span>
          </div>
          <Progress value={metrics.budgetUsed} className="h-1" />
        </div>
        
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="text-center">
            <div className="font-medium">{campaign.impressions.toLocaleString()}</div>
            <div className="text-muted-foreground">Impressions</div>
          </div>
          <div className="text-center">
            <div className="font-medium">{metrics.ctr.toFixed(2)}%</div>
            <div className="text-muted-foreground">CTR</div>
          </div>
          <div className="text-center">
            <div className="font-medium">{metrics.cvr.toFixed(2)}%</div>
            <div className="text-muted-foreground">CVR</div>
          </div>
        </div>
        
        <div className="flex space-x-2 pt-2">
          <Button 
            size="sm" 
            variant="ghost" 
            onClick={handleToggle}
            className="flex-1"
          >
            {campaign.status === 'active' ? 'Pause' : 'Resume'}
          </Button>
          <Button 
            size="sm" 
            variant="outline" 
            onClick={handleEdit}
          >
            Edit
          </Button>
        </div>
      </CardContent>
    </Card>
  );
});

OptimizedCampaignCard.displayName = 'OptimizedCampaignCard';

// Componente de Metric otimizado
export const OptimizedMetricCard = memo<MetricCardProps>(({ 
  title, 
  value, 
  description, 
  trend, 
  icon, 
  loading = false, 
  className 
}) => {
  // Memoizar formatação do valor
  const formattedValue = useMemo(() => {
    if (loading) return '...';
    if (typeof value === 'number') {
      return value.toLocaleString();
    }
    return value;
  }, [value, loading]);

  // Memoizar cor da tendência
  const trendColor = useMemo(() => {
    if (trend === undefined) return '';
    return trend >= 0 ? 'text-green-600' : 'text-red-600';
  }, [trend]);

  const trendIcon = useMemo(() => {
    if (trend === undefined) return null;
    return (
      <TrendingUp 
        className={`h-3 w-3 ${trendColor} ${trend < 0 ? 'rotate-180' : ''}`} 
      />
    );
  }, [trend, trendColor]);

  return (
    <Card className={`hover:shadow-lg transition-shadow ${className}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{formattedValue}</div>
        <div className="flex items-center space-x-1 text-xs text-muted-foreground">
          {description && <span>{description}</span>}
          {trend !== undefined && (
            <>
              {trendIcon}
              <span className={trendColor}>
                {Math.abs(trend).toFixed(1)}%
              </span>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
});

OptimizedMetricCard.displayName = 'OptimizedMetricCard';

// Lista otimizada de agentes
export const OptimizedAgentList = memo<{
  agents: Agent[];
  onStatusChange?: (agentId: string, status: Agent['status']) => void;
  onEdit?: (agentId: string) => void;
  className?: string;
}>(({ agents, onStatusChange, onEdit, className }) => {
  return (
    <div className={`grid gap-4 md:grid-cols-2 lg:grid-cols-3 ${className}`}>
      {agents.map((agent) => (
        <OptimizedAgentCard
          key={agent.id}
          agent={agent}
          onStatusChange={onStatusChange}
          onEdit={onEdit}
        />
      ))}
    </div>
  );
});

OptimizedAgentList.displayName = 'OptimizedAgentList';

// Lista otimizada de tasks
export const OptimizedTaskList = memo<{
  tasks: Task[];
  agents: Agent[];
  onRetry?: (taskId: string) => void;
  onCancel?: (taskId: string) => void;
  className?: string;
}>(({ tasks, agents, onRetry, onCancel, className }) => {
  // Memoizar mapa de agentes para performance
  const agentMap = useMemo(() => {
    return agents.reduce((map, agent) => {
      map[agent.id] = agent.name;
      return map;
    }, {} as Record<string, string>);
  }, [agents]);

  return (
    <div className={`space-y-2 ${className}`}>
      {tasks.map((task) => (
        <OptimizedTaskItem
          key={task.id}
          task={task}
          agentName={agentMap[task.agentId]}
          onRetry={onRetry}
          onCancel={onCancel}
        />
      ))}
    </div>
  );
});

OptimizedTaskList.displayName = 'OptimizedTaskList';
