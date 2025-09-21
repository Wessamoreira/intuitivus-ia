/**
 * Optimized Agent Card Component
 * Componente otimizado com React.memo e callbacks memoizados
 */

import React, { memo, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  Bot, 
  Play, 
  Pause, 
  Settings, 
  TrendingUp, 
  Clock,
  CheckCircle,
  AlertCircle 
} from 'lucide-react';
import { Agent } from '@/stores/types';

interface OptimizedAgentCardProps {
  agent: Agent;
  onStatusChange: (agentId: string, newStatus: string) => void;
  onEdit: (agentId: string) => void;
  onViewDetails: (agentId: string) => void;
  className?: string;
}

export const OptimizedAgentCard = memo<OptimizedAgentCardProps>(({ 
  agent, 
  onStatusChange, 
  onEdit, 
  onViewDetails,
  className = ""
}) => {
  // Callbacks memoizados para evitar re-renders desnecessários
  const handleStatusToggle = useCallback(() => {
    const newStatus = agent.status === 'active' ? 'inactive' : 'active';
    onStatusChange(agent.id, newStatus);
  }, [agent.id, agent.status, onStatusChange]);

  const handleEdit = useCallback(() => {
    onEdit(agent.id);
  }, [agent.id, onEdit]);

  const handleViewDetails = useCallback(() => {
    onViewDetails(agent.id);
  }, [agent.id, onViewDetails]);

  // Valores computados memoizados
  const statusConfig = useMemo(() => {
    switch (agent.status) {
      case 'active':
        return {
          color: 'bg-green-500',
          icon: CheckCircle,
          label: 'Ativo',
          variant: 'default' as const
        };
      case 'inactive':
        return {
          color: 'bg-gray-500',
          icon: Pause,
          label: 'Inativo',
          variant: 'secondary' as const
        };
      case 'error':
        return {
          color: 'bg-red-500',
          icon: AlertCircle,
          label: 'Erro',
          variant: 'destructive' as const
        };
      default:
        return {
          color: 'bg-yellow-500',
          icon: Clock,
          label: 'Processando',
          variant: 'outline' as const
        };
    }
  }, [agent.status]);

  const performanceMetrics = useMemo(() => {
    const tasksCompleted = agent.tasksCompleted || 0;
    const tasksTotal = agent.tasksTotal || 0;
    const successRate = tasksTotal > 0 ? Math.round((tasksCompleted / tasksTotal) * 100) : 0;
    
    return {
      tasksCompleted,
      tasksTotal,
      successRate,
      isHighPerformer: successRate >= 80
    };
  }, [agent.tasksCompleted, agent.tasksTotal]);

  const agentInitials = useMemo(() => {
    return agent.name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  }, [agent.name]);

  const StatusIcon = statusConfig.icon;

  return (
    <Card className={`hover:shadow-lg transition-all duration-200 ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Avatar className="h-10 w-10">
              <AvatarImage src={agent.avatar} alt={agent.name} />
              <AvatarFallback className="bg-primary/10 text-primary font-semibold">
                {agentInitials}
              </AvatarFallback>
            </Avatar>
            
            <div>
              <CardTitle className="text-lg font-semibold">{agent.name}</CardTitle>
              <p className="text-sm text-muted-foreground">{agent.type}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Badge variant={statusConfig.variant} className="flex items-center space-x-1">
              <StatusIcon className="h-3 w-3" />
              <span>{statusConfig.label}</span>
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Descrição */}
        {agent.description && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {agent.description}
          </p>
        )}

        {/* Métricas de Performance */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Tarefas Concluídas</p>
            <p className="text-lg font-semibold">
              {performanceMetrics.tasksCompleted}
              <span className="text-sm text-muted-foreground">
                /{performanceMetrics.tasksTotal}
              </span>
            </p>
          </div>
          
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Taxa de Sucesso</p>
            <div className="flex items-center space-x-2">
              <p className="text-lg font-semibold">{performanceMetrics.successRate}%</p>
              {performanceMetrics.isHighPerformer && (
                <TrendingUp className="h-4 w-4 text-green-500" />
              )}
            </div>
          </div>
        </div>

        {/* Última Atividade */}
        {agent.lastActivity && (
          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>Última atividade: {new Date(agent.lastActivity).toLocaleString()}</span>
          </div>
        )}

        {/* Ações */}
        <div className="flex items-center justify-between pt-2 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={handleViewDetails}
            className="flex items-center space-x-1"
          >
            <Bot className="h-4 w-4" />
            <span>Detalhes</span>
          </Button>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleEdit}
              className="flex items-center space-x-1"
            >
              <Settings className="h-4 w-4" />
              <span>Editar</span>
            </Button>
            
            <Button
              variant={agent.status === 'active' ? 'destructive' : 'default'}
              size="sm"
              onClick={handleStatusToggle}
              className="flex items-center space-x-1"
            >
              {agent.status === 'active' ? (
                <>
                  <Pause className="h-4 w-4" />
                  <span>Pausar</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  <span>Ativar</span>
                </>
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
});

OptimizedAgentCard.displayName = 'OptimizedAgentCard';
