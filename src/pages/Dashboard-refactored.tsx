import AppLayout from "@/components/layout/AppLayout";
import { DashboardStats } from "@/components/dashboard/DashboardStats";
import { DashboardCharts } from "@/components/dashboard/DashboardCharts";
import { DashboardAgents } from "@/components/dashboard/DashboardAgents";
import { useDashboardData } from "@/hooks/useDashboardData";

const Dashboard = () => {
  const {
    stats,
    tokenUsageData,
    campaignData,
    agentPerformanceData,
    agents,
    recentActivity,
    isLoading,
    completionRate,
    activeAgentsPercentage
  } = useDashboardData();

  return (
    <AppLayout>
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        </div>
        
        {/* Stats Cards */}
        <DashboardStats 
          stats={stats}
          completionRate={completionRate}
          activeAgentsPercentage={activeAgentsPercentage}
          isLoading={isLoading}
        />

        {/* Charts */}
        <DashboardCharts 
          tokenUsageData={tokenUsageData}
          campaignData={campaignData}
          agentPerformanceData={agentPerformanceData}
          isLoading={isLoading}
        />

        {/* Agents and Activity */}
        <DashboardAgents 
          agents={agents}
          recentActivity={recentActivity}
          isLoading={isLoading}
        />
      </div>
    </AppLayout>
  );
};

export default Dashboard;
