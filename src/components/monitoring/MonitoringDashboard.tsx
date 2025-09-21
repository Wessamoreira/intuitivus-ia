import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Cpu,
  Database,
  HardDrive,
  MemoryStick,
  Network,
  RefreshCw,
  Server,
  TrendingUp,
  Users,
  Zap
} from 'lucide-react';

// Types para métricas
interface Metric {
  name: string;
  value: number;
  timestamp: string;
  type: string;
  unit: string;
  labels?: Record<string, string>;
}

interface Alert {
  name: string;
  condition: string;
  threshold: number;
  current_value: number;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string;
  resolved: boolean;
}

interface MetricHistory {
  timestamp: string;
  value: number;
}

// Hook para métricas em tempo real
const useRealTimeMetrics = (refreshInterval: number = 30000) => {
  const [metrics, setMetrics] = useState<Record<string, Metric>>({});
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      // Simular API call - substituir por chamada real
      const mockMetrics = {
        system_cpu_usage_percent: {
          name: 'system_cpu_usage_percent',
          value: Math.random() * 100,
          timestamp: new Date().toISOString(),
          type: 'gauge',
          unit: '%'
        },
        system_memory_usage_percent: {
          name: 'system_memory_usage_percent',
          value: 65 + Math.random() * 20,
          timestamp: new Date().toISOString(),
          type: 'gauge',
          unit: '%'
        },
        system_disk_usage_percent: {
          name: 'system_disk_usage_percent',
          value: 45 + Math.random() * 10,
          timestamp: new Date().toISOString(),
          type: 'gauge',
          unit: '%'
        },
        cache_hit_rate_percent: {
          name: 'cache_hit_rate_percent',
          value: 85 + Math.random() * 10,
          timestamp: new Date().toISOString(),
          type: 'gauge',
          unit: '%'
        },
        business_active_users_total: {
          name: 'business_active_users_total',
          value: 150 + Math.floor(Math.random() * 50),
          timestamp: new Date().toISOString(),
          type: 'gauge',
          unit: ''
        },
        business_success_rate_percent: {
          name: 'business_success_rate_percent',
          value: 92 + Math.random() * 6,
          timestamp: new Date().toISOString(),
          type: 'gauge',
          unit: '%'
        },
        db_pool_checked_out: {
          name: 'db_pool_checked_out',
          value: Math.floor(Math.random() * 20),
          timestamp: new Date().toISOString(),
          type: 'gauge',
          unit: ''
        },
        app_uptime_seconds: {
          name: 'app_uptime_seconds',
          value: Date.now() / 1000,
          timestamp: new Date().toISOString(),
          type: 'gauge',
          unit: 's'
        }
      };

      setMetrics(mockMetrics);
      
      // Mock alerts
      const mockAlerts: Alert[] = [];
      if (mockMetrics.system_cpu_usage_percent.value > 80) {
        mockAlerts.push({
          name: 'high_cpu_usage',
          condition: 'system_cpu_usage_percent > 80',
          threshold: 80,
          current_value: mockMetrics.system_cpu_usage_percent.value,
          severity: 'warning',
          message: 'High CPU usage detected',
          timestamp: new Date().toISOString(),
          resolved: false
        });
      }

      setAlerts(mockAlerts);
      setError(null);
    } catch (err) {
      setError('Failed to fetch metrics');
      console.error('Error fetching metrics:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchMetrics, refreshInterval]);

  return { metrics, alerts, loading, error, refetch: fetchMetrics };
};

// Hook para histórico de métricas
const useMetricHistory = (metricName: string, hours: number = 1) => {
  const [history, setHistory] = useState<MetricHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        // Simular dados históricos
        const now = Date.now();
        const mockHistory: MetricHistory[] = [];
        
        for (let i = hours * 60; i >= 0; i -= 5) { // Pontos a cada 5 minutos
          const timestamp = new Date(now - i * 60 * 1000).toISOString();
          let value = 50;
          
          // Simular padrões diferentes por métrica
          if (metricName.includes('cpu')) {
            value = 30 + Math.sin(i / 10) * 20 + Math.random() * 10;
          } else if (metricName.includes('memory')) {
            value = 60 + Math.sin(i / 15) * 15 + Math.random() * 5;
          } else if (metricName.includes('success_rate')) {
            value = 95 + Math.sin(i / 20) * 3 + Math.random() * 2;
          }
          
          mockHistory.push({ timestamp, value: Math.max(0, Math.min(100, value)) });
        }
        
        setHistory(mockHistory);
      } catch (err) {
        console.error('Error fetching metric history:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [metricName, hours]);

  return { history, loading };
};

// Componente de métrica individual
const MetricCard: React.FC<{
  title: string;
  value: number;
  unit: string;
  icon: React.ReactNode;
  threshold?: { warning: number; critical: number };
  trend?: number;
}> = ({ title, value, unit, icon, threshold, trend }) => {
  const getStatusColor = () => {
    if (!threshold) return 'text-green-600';
    if (value >= threshold.critical) return 'text-red-600';
    if (value >= threshold.warning) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getProgressColor = () => {
    if (!threshold) return '';
    if (value >= threshold.critical) return 'bg-red-500';
    if (value >= threshold.warning) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${getStatusColor()}`}>
          {value.toFixed(1)}{unit}
        </div>
        
        {threshold && unit === '%' && (
          <div className="mt-2">
            <Progress 
              value={value} 
              className="h-2"
              // className={`h-2 ${getProgressColor()}`}
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>0%</span>
              <span className="text-yellow-600">{threshold.warning}%</span>
              <span className="text-red-600">{threshold.critical}%</span>
              <span>100%</span>
            </div>
          </div>
        )}
        
        {trend !== undefined && (
          <div className="flex items-center text-xs text-muted-foreground mt-2">
            <TrendingUp className={`h-3 w-3 mr-1 ${trend >= 0 ? 'text-green-500' : 'text-red-500 rotate-180'}`} />
            <span className={trend >= 0 ? 'text-green-500' : 'text-red-500'}>
              {Math.abs(trend).toFixed(1)}% from last hour
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Componente de gráfico de histórico
const MetricChart: React.FC<{
  title: string;
  metricName: string;
  color: string;
  unit: string;
}> = ({ title, metricName, color, unit }) => {
  const { history, loading } = useMetricHistory(metricName, 2); // 2 horas

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center">
            <RefreshCw className="h-6 w-6 animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>Last 2 hours</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={history}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={(value) => new Date(value).toLocaleTimeString()}
              fontSize={12}
            />
            <YAxis 
              domain={['dataMin - 5', 'dataMax + 5']}
              tickFormatter={(value) => `${value.toFixed(0)}${unit}`}
              fontSize={12}
            />
            <Tooltip 
              labelFormatter={(value) => new Date(value).toLocaleString()}
              formatter={(value: number) => [`${value.toFixed(2)}${unit}`, title]}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke={color}
              fill={color}
              fillOpacity={0.2}
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// Componente de alertas
const AlertsPanel: React.FC<{ alerts: Alert[] }> = ({ alerts }) => {
  const getSeverityIcon = (severity: Alert['severity']) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <CheckCircle className="h-4 w-4 text-blue-500" />;
    }
  };

  const getSeverityVariant = (severity: Alert['severity']) => {
    switch (severity) {
      case 'critical':
        return 'destructive';
      case 'warning':
        return 'default';
      default:
        return 'secondary';
    }
  };

  if (alerts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
            All Systems Operational
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No active alerts</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Active Alerts ({alerts.length})</h3>
      {alerts.map((alert, index) => (
        <Alert key={index} variant={getSeverityVariant(alert.severity)}>
          {getSeverityIcon(alert.severity)}
          <AlertTitle className="flex items-center justify-between">
            {alert.name}
            <Badge variant="outline">
              {alert.severity}
            </Badge>
          </AlertTitle>
          <AlertDescription>
            <div className="mt-2">
              <p>{alert.message}</p>
              <p className="text-sm mt-1">
                Current: {alert.current_value.toFixed(2)} | Threshold: {alert.threshold}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {new Date(alert.timestamp).toLocaleString()}
              </p>
            </div>
          </AlertDescription>
        </Alert>
      ))}
    </div>
  );
};

// Dashboard principal
export const MonitoringDashboard: React.FC = () => {
  const { metrics, alerts, loading, error, refetch } = useRealTimeMetrics();
  const [autoRefresh, setAutoRefresh] = useState(true);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading metrics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          {error}
          <Button variant="outline" size="sm" onClick={refetch} className="ml-2">
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">System Monitoring</h1>
          <p className="text-muted-foreground">
            Real-time system and application metrics
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <Activity className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-pulse' : ''}`} />
            Auto Refresh: {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button variant="outline" size="sm" onClick={refetch}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Alertas */}
      {alerts.length > 0 && (
        <AlertsPanel alerts={alerts} />
      )}

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="application">Application</TabsTrigger>
          <TabsTrigger value="business">Business</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Métricas principais */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="CPU Usage"
              value={metrics.system_cpu_usage_percent?.value || 0}
              unit="%"
              icon={<Cpu className="h-4 w-4" />}
              threshold={{ warning: 70, critical: 85 }}
            />
            <MetricCard
              title="Memory Usage"
              value={metrics.system_memory_usage_percent?.value || 0}
              unit="%"
              icon={<MemoryStick className="h-4 w-4" />}
              threshold={{ warning: 80, critical: 90 }}
            />
            <MetricCard
              title="Cache Hit Rate"
              value={metrics.cache_hit_rate_percent?.value || 0}
              unit="%"
              icon={<Database className="h-4 w-4" />}
              threshold={{ warning: 70, critical: 50 }}
            />
            <MetricCard
              title="Success Rate"
              value={metrics.business_success_rate_percent?.value || 0}
              unit="%"
              icon={<CheckCircle className="h-4 w-4" />}
              threshold={{ warning: 90, critical: 85 }}
            />
          </div>

          {/* Gráficos */}
          <div className="grid gap-4 md:grid-cols-2">
            <MetricChart
              title="CPU Usage"
              metricName="system_cpu_usage_percent"
              color="#3b82f6"
              unit="%"
            />
            <MetricChart
              title="Memory Usage"
              metricName="system_memory_usage_percent"
              color="#10b981"
              unit="%"
            />
          </div>
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <MetricCard
              title="CPU Usage"
              value={metrics.system_cpu_usage_percent?.value || 0}
              unit="%"
              icon={<Cpu className="h-4 w-4" />}
              threshold={{ warning: 70, critical: 85 }}
            />
            <MetricCard
              title="Memory Usage"
              value={metrics.system_memory_usage_percent?.value || 0}
              unit="%"
              icon={<MemoryStick className="h-4 w-4" />}
              threshold={{ warning: 80, critical: 90 }}
            />
            <MetricCard
              title="Disk Usage"
              value={metrics.system_disk_usage_percent?.value || 0}
              unit="%"
              icon={<HardDrive className="h-4 w-4" />}
              threshold={{ warning: 80, critical: 90 }}
            />
          </div>
        </TabsContent>

        <TabsContent value="application" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <MetricCard
              title="DB Connections"
              value={metrics.db_pool_checked_out?.value || 0}
              unit=""
              icon={<Database className="h-4 w-4" />}
            />
            <MetricCard
              title="Cache Hit Rate"
              value={metrics.cache_hit_rate_percent?.value || 0}
              unit="%"
              icon={<Zap className="h-4 w-4" />}
              threshold={{ warning: 70, critical: 50 }}
            />
            <MetricCard
              title="Uptime"
              value={(metrics.app_uptime_seconds?.value || 0) / 3600}
              unit="h"
              icon={<Clock className="h-4 w-4" />}
            />
          </div>
        </TabsContent>

        <TabsContent value="business" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <MetricCard
              title="Active Users"
              value={metrics.business_active_users_total?.value || 0}
              unit=""
              icon={<Users className="h-4 w-4" />}
            />
            <MetricCard
              title="Success Rate"
              value={metrics.business_success_rate_percent?.value || 0}
              unit="%"
              icon={<CheckCircle className="h-4 w-4" />}
              threshold={{ warning: 90, critical: 85 }}
            />
            <MetricCard
              title="System Health"
              value={alerts.length === 0 ? 100 : Math.max(0, 100 - alerts.length * 10)}
              unit="%"
              icon={<Activity className="h-4 w-4" />}
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
