/**
 * Testes para componentes otimizados
 * Testa funcionalidade, performance e acessibilidade
 */

import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { render, createUserEvent, mockAgents, mockTasks, mockCampaigns, checkAccessibility } from '../utils/test-utils';
import {
  OptimizedAgentCard,
  OptimizedTaskItem,
  OptimizedCampaignCard,
  OptimizedMetricCard,
  OptimizedAgentList,
  OptimizedTaskList
} from '@/components/optimized/OptimizedComponents';

describe('OptimizedAgentCard', () => {
  const mockAgent = mockAgents[0];
  
  it('renders agent information correctly', () => {
    render(<OptimizedAgentCard agent={mockAgent} />);
    
    expect(screen.getByText(mockAgent.name)).toBeInTheDocument();
    expect(screen.getByText(mockAgent.type)).toBeInTheDocument();
    expect(screen.getByText(mockAgent.status)).toBeInTheDocument();
    expect(screen.getByText(`${mockAgent.successRate}%`)).toBeInTheDocument();
    expect(screen.getByText(`${mockAgent.tasksCompleted} tasks completed`)).toBeInTheDocument();
  });
  
  it('displays correct status badge variant', () => {
    const activeAgent = { ...mockAgent, status: 'active' as const };
    const pausedAgent = { ...mockAgent, status: 'paused' as const };
    
    const { rerender } = render(<OptimizedAgentCard agent={activeAgent} />);
    expect(screen.getByText('active')).toHaveClass('bg-primary');
    
    rerender(<OptimizedAgentCard agent={pausedAgent} />);
    expect(screen.getByText('paused')).toHaveClass('bg-secondary');
  });
  
  it('calls onStatusChange when toggle button is clicked', async () => {
    const user = createUserEvent();
    const onStatusChange = jest.fn();
    
    render(
      <OptimizedAgentCard 
        agent={mockAgent} 
        onStatusChange={onStatusChange}
      />
    );
    
    const toggleButton = screen.getByRole('button', { name: /pause/i });
    await user.click(toggleButton);
    
    expect(onStatusChange).toHaveBeenCalledWith(mockAgent.id, 'paused');
  });
  
  it('calls onEdit when edit button is clicked', async () => {
    const user = createUserEvent();
    const onEdit = jest.fn();
    
    render(
      <OptimizedAgentCard 
        agent={mockAgent} 
        onEdit={onEdit}
      />
    );
    
    const editButton = screen.getByRole('button', { name: /edit/i });
    await user.click(editButton);
    
    expect(onEdit).toHaveBeenCalledWith(mockAgent.id);
  });
  
  it('shows correct button text based on status', () => {
    const activeAgent = { ...mockAgent, status: 'active' as const };
    const pausedAgent = { ...mockAgent, status: 'paused' as const };
    
    const { rerender } = render(<OptimizedAgentCard agent={activeAgent} />);
    expect(screen.getByText('Pause')).toBeInTheDocument();
    
    rerender(<OptimizedAgentCard agent={pausedAgent} />);
    expect(screen.getByText('Start')).toBeInTheDocument();
  });
  
  it('is accessible', async () => {
    const { container } = render(<OptimizedAgentCard agent={mockAgent} />);
    await checkAccessibility(container);
  });
});

describe('OptimizedTaskItem', () => {
  const mockTask = mockTasks[0];
  const agentName = 'Test Agent';
  
  it('renders task information correctly', () => {
    render(
      <OptimizedTaskItem 
        task={mockTask} 
        agentName={agentName}
      />
    );
    
    expect(screen.getByText(mockTask.type)).toBeInTheDocument();
    expect(screen.getByText(mockTask.status)).toBeInTheDocument();
    expect(screen.getByText(agentName)).toBeInTheDocument();
  });
  
  it('shows execution time for completed tasks', () => {
    const completedTask = { ...mockTask, status: 'completed' as const, executionTime: 1250 };
    
    render(<OptimizedTaskItem task={completedTask} />);
    
    expect(screen.getByText('Execution time: 1250ms')).toBeInTheDocument();
  });
  
  it('shows error message for failed tasks', () => {
    const failedTask = { 
      ...mockTask, 
      status: 'failed' as const, 
      error: 'API rate limit exceeded' 
    };
    
    render(<OptimizedTaskItem task={failedTask} />);
    
    expect(screen.getByText(/API rate limit exceeded/)).toBeInTheDocument();
  });
  
  it('shows retry button for failed tasks', async () => {
    const user = createUserEvent();
    const onRetry = jest.fn();
    const failedTask = { ...mockTask, status: 'failed' as const };
    
    render(
      <OptimizedTaskItem 
        task={failedTask} 
        onRetry={onRetry}
      />
    );
    
    const retryButton = screen.getByRole('button', { name: /retry/i });
    await user.click(retryButton);
    
    expect(onRetry).toHaveBeenCalledWith(failedTask.id);
  });
  
  it('shows cancel button for running tasks', async () => {
    const user = createUserEvent();
    const onCancel = jest.fn();
    const runningTask = { ...mockTask, status: 'running' as const };
    
    render(
      <OptimizedTaskItem 
        task={runningTask} 
        onCancel={onCancel}
      />
    );
    
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);
    
    expect(onCancel).toHaveBeenCalledWith(runningTask.id);
  });
  
  it('displays correct status icon', () => {
    const completedTask = { ...mockTask, status: 'completed' as const };
    const runningTask = { ...mockTask, status: 'running' as const };
    
    const { rerender } = render(<OptimizedTaskItem task={completedTask} />);
    expect(screen.getByTestId('check-circle-icon')).toBeInTheDocument();
    
    rerender(<OptimizedTaskItem task={runningTask} />);
    expect(screen.getByTestId('activity-icon')).toBeInTheDocument();
  });
});

describe('OptimizedCampaignCard', () => {
  const mockCampaign = mockCampaigns[0];
  
  it('renders campaign information correctly', () => {
    render(<OptimizedCampaignCard campaign={mockCampaign} />);
    
    expect(screen.getByText(mockCampaign.name)).toBeInTheDocument();
    expect(screen.getByText(mockCampaign.status)).toBeInTheDocument();
    expect(screen.getByText(`$${mockCampaign.budget.toLocaleString()}`)).toBeInTheDocument();
    expect(screen.getByText(`$${mockCampaign.spent.toLocaleString()}`)).toBeInTheDocument();
  });
  
  it('calculates and displays metrics correctly', () => {
    render(<OptimizedCampaignCard campaign={mockCampaign} />);
    
    const expectedCTR = (mockCampaign.clicks / mockCampaign.impressions * 100).toFixed(2);
    const expectedCVR = (mockCampaign.conversions / mockCampaign.clicks * 100).toFixed(2);
    const expectedBudgetUsage = (mockCampaign.spent / mockCampaign.budget * 100);
    
    expect(screen.getByText(`${expectedCTR}%`)).toBeInTheDocument();
    expect(screen.getByText(`${expectedCVR}%`)).toBeInTheDocument();
    expect(screen.getByText(`${expectedBudgetUsage.toFixed(1)}%`)).toBeInTheDocument();
  });
  
  it('calls onPause for active campaigns', async () => {
    const user = createUserEvent();
    const onPause = jest.fn();
    const activeCampaign = { ...mockCampaign, status: 'active' as const };
    
    render(
      <OptimizedCampaignCard 
        campaign={activeCampaign} 
        onPause={onPause}
      />
    );
    
    const pauseButton = screen.getByRole('button', { name: /pause/i });
    await user.click(pauseButton);
    
    expect(onPause).toHaveBeenCalledWith(activeCampaign.id);
  });
  
  it('calls onResume for paused campaigns', async () => {
    const user = createUserEvent();
    const onResume = jest.fn();
    const pausedCampaign = { ...mockCampaign, status: 'paused' as const };
    
    render(
      <OptimizedCampaignCard 
        campaign={pausedCampaign} 
        onResume={onResume}
      />
    );
    
    const resumeButton = screen.getByRole('button', { name: /resume/i });
    await user.click(resumeButton);
    
    expect(onResume).toHaveBeenCalledWith(pausedCampaign.id);
  });
});

describe('OptimizedMetricCard', () => {
  it('renders metric information correctly', () => {
    render(
      <OptimizedMetricCard
        title="Total Users"
        value={1234}
        description="Active users"
        trend={15.2}
      />
    );
    
    expect(screen.getByText('Total Users')).toBeInTheDocument();
    expect(screen.getByText('1,234')).toBeInTheDocument();
    expect(screen.getByText('Active users')).toBeInTheDocument();
    expect(screen.getByText('15.2%')).toBeInTheDocument();
  });
  
  it('shows loading state', () => {
    render(
      <OptimizedMetricCard
        title="Loading Metric"
        value={0}
        loading={true}
      />
    );
    
    expect(screen.getByText('...')).toBeInTheDocument();
  });
  
  it('handles negative trends correctly', () => {
    render(
      <OptimizedMetricCard
        title="Declining Metric"
        value={100}
        trend={-5.3}
      />
    );
    
    expect(screen.getByText('5.3%')).toBeInTheDocument();
    expect(screen.getByText('5.3%')).toHaveClass('text-red-600');
  });
  
  it('handles string values', () => {
    render(
      <OptimizedMetricCard
        title="Status"
        value="Active"
      />
    );
    
    expect(screen.getByText('Active')).toBeInTheDocument();
  });
});

describe('OptimizedAgentList', () => {
  it('renders all agents', () => {
    render(<OptimizedAgentList agents={mockAgents} />);
    
    mockAgents.forEach(agent => {
      expect(screen.getByText(agent.name)).toBeInTheDocument();
    });
  });
  
  it('handles empty agent list', () => {
    render(<OptimizedAgentList agents={[]} />);
    
    expect(screen.queryByText('Marketing Specialist')).not.toBeInTheDocument();
  });
  
  it('calls callbacks for all agents', async () => {
    const user = createUserEvent();
    const onStatusChange = jest.fn();
    const onEdit = jest.fn();
    
    render(
      <OptimizedAgentList 
        agents={mockAgents} 
        onStatusChange={onStatusChange}
        onEdit={onEdit}
      />
    );
    
    // Click first agent's toggle button
    const toggleButtons = screen.getAllByRole('button', { name: /pause|start/i });
    await user.click(toggleButtons[0]);
    
    expect(onStatusChange).toHaveBeenCalled();
  });
});

describe('OptimizedTaskList', () => {
  it('renders all tasks with agent names', () => {
    render(
      <OptimizedTaskList 
        tasks={mockTasks} 
        agents={mockAgents}
      />
    );
    
    mockTasks.forEach(task => {
      expect(screen.getByText(task.type)).toBeInTheDocument();
    });
    
    // Should show agent names
    expect(screen.getByText('Marketing Specialist')).toBeInTheDocument();
  });
  
  it('handles tasks with unknown agents', () => {
    const tasksWithUnknownAgent = [
      { ...mockTasks[0], agentId: 'unknown-agent' }
    ];
    
    render(
      <OptimizedTaskList 
        tasks={tasksWithUnknownAgent} 
        agents={mockAgents}
      />
    );
    
    expect(screen.getByText('Unknown Agent')).toBeInTheDocument();
  });
  
  it('handles empty task list', () => {
    render(
      <OptimizedTaskList 
        tasks={[]} 
        agents={mockAgents}
      />
    );
    
    expect(screen.queryByText('Campaign Analysis')).not.toBeInTheDocument();
  });
});

describe('Component Performance', () => {
  it('should not re-render unnecessarily', () => {
    const renderSpy = jest.fn();
    
    const TestComponent = React.memo(() => {
      renderSpy();
      return <OptimizedAgentCard agent={mockAgents[0]} />;
    });
    
    const { rerender } = render(<TestComponent />);
    
    expect(renderSpy).toHaveBeenCalledTimes(1);
    
    // Re-render with same props
    rerender(<TestComponent />);
    
    // Should not re-render due to memo
    expect(renderSpy).toHaveBeenCalledTimes(1);
  });
  
  it('should handle large lists efficiently', async () => {
    const largeAgentList = Array.from({ length: 1000 }, (_, i) => ({
      ...mockAgents[0],
      id: `agent-${i}`,
      name: `Agent ${i}`,
    }));
    
    const startTime = performance.now();
    
    render(<OptimizedAgentList agents={largeAgentList} />);
    
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // Should render in reasonable time (adjust threshold as needed)
    expect(renderTime).toBeLessThan(1000); // Less than 1 second
    
    // Should render first few agents
    expect(screen.getByText('Agent 0')).toBeInTheDocument();
    expect(screen.getByText('Agent 1')).toBeInTheDocument();
  });
});

describe('Accessibility', () => {
  it('all components should be accessible', async () => {
    const { container: agentContainer } = render(
      <OptimizedAgentCard agent={mockAgents[0]} />
    );
    await checkAccessibility(agentContainer);
    
    const { container: taskContainer } = render(
      <OptimizedTaskItem task={mockTasks[0]} />
    );
    await checkAccessibility(taskContainer);
    
    const { container: campaignContainer } = render(
      <OptimizedCampaignCard campaign={mockCampaigns[0]} />
    );
    await checkAccessibility(campaignContainer);
    
    const { container: metricContainer } = render(
      <OptimizedMetricCard title="Test" value={100} />
    );
    await checkAccessibility(metricContainer);
  });
});
