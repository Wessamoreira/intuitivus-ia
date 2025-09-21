import { useState, useEffect } from 'react';
import type { 
  DashboardStats, 
  TokenUsageData, 
  CampaignData, 
  AgentPerformanceData, 
  Agent, 
  RecentActivity 
} from '@/types/dashboard.types';

// Hook para gerenciar dados do dashboard
export const useDashboardData = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalAgents: 5,
    activeAgents: 3,
    totalTasks: 156,
    completedTasks: 142,
    totalRevenue: 12450,
    monthlyGrowth: 23.5
  });

  const [tokenUsageData] = useState<TokenUsageData[]>([
    { name: "Mon", usage: 1200, cost: 24 },
    { name: "Tue", usage: 1900, cost: 38 },
    { name: "Wed", usage: 800, cost: 16 },
    { name: "Thu", usage: 2780, cost: 55.6 },
    { name: "Fri", usage: 1890, cost: 37.8 },
    { name: "Sat", usage: 2390, cost: 47.8 },
    { name: "Sun", usage: 3490, cost: 69.8 },
  ]);

  const [campaignData] = useState<CampaignData[]>([
    { name: "Google Ads", value: 45, color: "#4285f4" },
    { name: "Meta Ads", value: 35, color: "#1877f2" },
    { name: "TikTok Ads", value: 20, color: "#ff0050" },
  ]);

  const [agentPerformanceData] = useState<AgentPerformanceData[]>([
    { name: "Marketing Agent", tasks: 12, success: 11 },
    { name: "Customer Service", tasks: 28, success: 26 },
    { name: "Content Creator", tasks: 8, success: 7 },
    { name: "Campaign Manager", tasks: 15, success: 14 },
  ]);

  const [agents] = useState<Agent[]>([
    {
      id: "1",
      name: "Marketing Specialist",
      status: "active",
      type: "Marketing",
      tasksCompleted: 45,
      lastActivity: "2 min ago",
      performance: 94
    },
    {
      id: "2", 
      name: "Customer Support Bot",
      status: "active",
      type: "Support",
      tasksCompleted: 128,
      lastActivity: "5 min ago",
      performance: 98
    },
    {
      id: "3",
      name: "Content Creator AI",
      status: "paused",
      type: "Content",
      tasksCompleted: 23,
      lastActivity: "1 hour ago",
      performance: 87
    }
  ]);

  const [recentActivity] = useState<RecentActivity[]>([
    {
      id: "1",
      type: "task_completed",
      message: "Marketing campaign analysis completed",
      timestamp: "2 minutes ago",
      agentName: "Marketing Specialist"
    },
    {
      id: "2",
      type: "agent_created",
      message: "New customer support agent deployed",
      timestamp: "15 minutes ago"
    },
    {
      id: "3",
      type: "campaign_started",
      message: "Google Ads campaign launched",
      timestamp: "1 hour ago"
    }
  ]);

  const [isLoading, setIsLoading] = useState(true);

  // Simular carregamento de dados
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  // Função para atualizar stats
  const updateStats = (newStats: Partial<DashboardStats>): void => {
    setStats(prev => ({ ...prev, ...newStats }));
  };

  // Calcular métricas derivadas
  const completionRate = Math.round((stats.completedTasks / stats.totalTasks) * 100);
  const activeAgentsPercentage = Math.round((stats.activeAgents / stats.totalAgents) * 100);

  return {
    // Dados
    stats,
    tokenUsageData,
    campaignData,
    agentPerformanceData,
    agents,
    recentActivity,
    
    // Estados
    isLoading,
    
    // Métricas calculadas
    completionRate,
    activeAgentsPercentage,
    
    // Ações
    updateStats,
  };
};
