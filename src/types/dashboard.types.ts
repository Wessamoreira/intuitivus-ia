// Types para o Dashboard e componentes relacionados

export interface TokenUsageData {
  name: string;
  usage: number;
  cost: number;
}

export interface CampaignData {
  name: string;
  value: number;
  color: string;
}

export interface AgentPerformanceData {
  name: string;
  tasks: number;
  success: number;
}

export interface DashboardStats {
  totalAgents: number;
  activeAgents: number;
  totalTasks: number;
  completedTasks: number;
  totalRevenue: number;
  monthlyGrowth: number;
}

export interface Agent {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'paused';
  type: string;
  tasksCompleted: number;
  lastActivity: string;
  performance: number;
}

export interface RecentActivity {
  id: string;
  type: 'task_completed' | 'agent_created' | 'campaign_started' | 'error';
  message: string;
  timestamp: string;
  agentName?: string;
}
