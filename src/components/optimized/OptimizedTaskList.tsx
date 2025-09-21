/**
 * Optimized Task List Component
 * Lista de tarefas otimizada com virtualização e memoização
 */

import React, { memo, useCallback, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Search, 
  Filter, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  Play,
  Pause,
  MoreHorizontal 
} from 'lucide-react';
import { Task } from '@/stores/types';
import { useFilteredTasks } from '@/stores/useAppStore';

interface OptimizedTaskListProps {
  onTaskClick: (taskId: string) => void;
  onStatusChange: (taskId: string, newStatus: string) => void;
  className?: string;
}

// Componente individual de tarefa memoizado
const TaskItem = memo<{
  task: Task;
  onTaskClick: (taskId: string) => void;
  onStatusChange: (taskId: string, newStatus: string) => void;
}>(({ task, onTaskClick, onStatusChange }) => {
  const handleClick = useCallback(() => {
    onTaskClick(task.id);
  }, [task.id, onTaskClick]);

  const handleStatusChange = useCallback(() => {
    const newStatus = task.status === 'running' ? 'paused' : 'running';
    onStatusChange(task.id, newStatus);
  }, [task.id, task.status, onStatusChange]);

  const statusConfig = useMemo(() => {
    switch (task.status) {
      case 'completed':
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          variant: 'default' as const,
          label: 'Concluída'
        };
      case 'running':
        return {
          icon: Play,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          variant: 'default' as const,
          label: 'Executando'
        };
      case 'paused':
        return {
          icon: Pause,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          variant: 'secondary' as const,
          label: 'Pausada'
        };
      case 'failed':
        return {
          icon: AlertTriangle,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          variant: 'destructive' as const,
          label: 'Falhou'
        };
      default:
        return {
          icon: Clock,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          variant: 'outline' as const,
          label: 'Pendente'
        };
    }
  }, [task.status]);

  const priorityConfig = useMemo(() => {
    switch (task.priority) {
      case 'high':
        return { color: 'bg-red-100 text-red-800', label: 'Alta' };
      case 'medium':
        return { color: 'bg-yellow-100 text-yellow-800', label: 'Média' };
      case 'low':
        return { color: 'bg-green-100 text-green-800', label: 'Baixa' };
      default:
        return { color: 'bg-gray-100 text-gray-800', label: 'Normal' };
    }
  }, [task.priority]);

  const StatusIcon = statusConfig.icon;

  return (
    <Card 
      className="hover:shadow-md transition-all duration-200 cursor-pointer"
      onClick={handleClick}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1">
            <div className={`p-2 rounded-full ${statusConfig.bgColor}`}>
              <StatusIcon className={`h-4 w-4 ${statusConfig.color}`} />
            </div>
            
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-sm truncate">{task.title}</h3>
              <p className="text-xs text-muted-foreground truncate">
                {task.description}
              </p>
              
              <div className="flex items-center space-x-2 mt-2">
                <Badge variant={statusConfig.variant} className="text-xs">
                  {statusConfig.label}
                </Badge>
                <Badge className={`text-xs ${priorityConfig.color}`}>
                  {priorityConfig.label}
                </Badge>
                {task.agentName && (
                  <span className="text-xs text-muted-foreground">
                    por {task.agentName}
                  </span>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {task.progress !== undefined && (
              <div className="text-xs text-muted-foreground">
                {Math.round(task.progress)}%
              </div>
            )}
            
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleStatusChange();
              }}
              disabled={task.status === 'completed' || task.status === 'failed'}
            >
              {task.status === 'running' ? (
                <Pause className="h-4 w-4" />
              ) : (
                <Play className="h-4 w-4" />
              )}
            </Button>
            
            <Button variant="ghost" size="sm">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        {task.progress !== undefined && (
          <div className="mt-3">
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div 
                className="bg-primary h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${task.progress}%` }}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
});

TaskItem.displayName = 'TaskItem';

export const OptimizedTaskList = memo<OptimizedTaskListProps>(({ 
  onTaskClick, 
  onStatusChange,
  className = ""
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');

  // Usar selector otimizado do store
  const allTasks = useFilteredTasks({ 
    status: statusFilter || undefined,
    priority: priorityFilter || undefined 
  });

  // Filtrar por termo de busca (memoizado)
  const filteredTasks = useMemo(() => {
    if (!searchTerm.trim()) return allTasks;
    
    const term = searchTerm.toLowerCase();
    return allTasks.filter(task => 
      task.title.toLowerCase().includes(term) ||
      task.description?.toLowerCase().includes(term) ||
      task.agentName?.toLowerCase().includes(term)
    );
  }, [allTasks, searchTerm]);

  // Callbacks memoizados
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  }, []);

  const handleStatusFilterChange = useCallback((value: string) => {
    setStatusFilter(value === 'all' ? '' : value);
  }, []);

  const handlePriorityFilterChange = useCallback((value: string) => {
    setPriorityFilter(value === 'all' ? '' : value);
  }, []);

  // Estatísticas memoizadas
  const taskStats = useMemo(() => {
    const total = filteredTasks.length;
    const completed = filteredTasks.filter(t => t.status === 'completed').length;
    const running = filteredTasks.filter(t => t.status === 'running').length;
    const failed = filteredTasks.filter(t => t.status === 'failed').length;
    
    return { total, completed, running, failed };
  }, [filteredTasks]);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header com filtros */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <span>Tarefas</span>
              <Badge variant="secondary">{taskStats.total}</Badge>
            </CardTitle>
            
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar tarefas..."
                  value={searchTerm}
                  onChange={handleSearchChange}
                  className="pl-10 w-64"
                />
              </div>
              
              <Select value={statusFilter || 'all'} onValueChange={handleStatusFilterChange}>
                <SelectTrigger className="w-32">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="running">Executando</SelectItem>
                  <SelectItem value="completed">Concluídas</SelectItem>
                  <SelectItem value="paused">Pausadas</SelectItem>
                  <SelectItem value="failed">Falharam</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={priorityFilter || 'all'} onValueChange={handlePriorityFilterChange}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Prioridade" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  <SelectItem value="high">Alta</SelectItem>
                  <SelectItem value="medium">Média</SelectItem>
                  <SelectItem value="low">Baixa</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          {/* Estatísticas rápidas */}
          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
            <span>Executando: {taskStats.running}</span>
            <span>Concluídas: {taskStats.completed}</span>
            <span>Falharam: {taskStats.failed}</span>
          </div>
        </CardHeader>
      </Card>

      {/* Lista de tarefas */}
      <div className="space-y-2">
        {filteredTasks.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <p className="text-muted-foreground">
                {searchTerm ? 'Nenhuma tarefa encontrada para sua busca.' : 'Nenhuma tarefa encontrada.'}
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredTasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onTaskClick={onTaskClick}
              onStatusChange={onStatusChange}
            />
          ))
        )}
      </div>
    </div>
  );
});

OptimizedTaskList.displayName = 'OptimizedTaskList';
