"""
Metrics Collector - Sistema de Monitoramento
Coleta métricas de performance, negócio e sistema em tempo real
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import psutil
import logging

from app.infrastructure.cache.cache_manager import cache_manager
from app.infrastructure.database.connection_manager import db_manager


class MetricType(str, Enum):
    """Tipos de métricas"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """Estrutura de uma métrica"""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unit: str = ""
    description: str = ""


@dataclass
class Alert:
    """Estrutura de um alerta"""
    name: str
    condition: str
    threshold: float
    current_value: float
    severity: str  # critical, warning, info
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False


class MetricsCollector:
    """
    Coletor de métricas em tempo real
    
    Funcionalidades:
    - Coleta métricas de sistema, aplicação e negócio
    - Armazenamento em Redis com TTL
    - Alertas baseados em thresholds
    - Agregações e estatísticas
    - Export para sistemas externos
    """
    
    def __init__(self):
        self.metrics: Dict[str, List[Metric]] = {}
        self.alerts: List[Alert] = []
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.collection_interval = 30  # segundos
        self.retention_period = 24 * 60 * 60  # 24 horas
        self.logger = logging.getLogger(__name__)
        self._collection_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start_collection(self):
        """Inicia coleta automática de métricas"""
        if self._is_running:
            return
        
        self._is_running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        self.logger.info("Metrics collection started")
    
    async def stop_collection(self):
        """Para coleta de métricas"""
        self._is_running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Metrics collection stopped")
    
    async def _collection_loop(self):
        """Loop principal de coleta"""
        while self._is_running:
            try:
                await self.collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                self.logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(5)  # Retry em 5s
    
    async def collect_all_metrics(self):
        """Coleta todas as métricas"""
        await asyncio.gather(
            self.collect_system_metrics(),
            self.collect_application_metrics(),
            self.collect_business_metrics(),
            self.collect_database_metrics(),
            self.collect_cache_metrics(),
            return_exceptions=True
        )
        
        # Verificar alertas
        await self.check_alerts()
        
        # Persistir métricas
        await self.persist_metrics()
    
    async def collect_system_metrics(self):
        """Coleta métricas do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            await self.record_metric(
                "system_cpu_usage_percent",
                MetricType.GAUGE,
                cpu_percent,
                description="CPU usage percentage"
            )
            
            # Memória
            memory = psutil.virtual_memory()
            await self.record_metric(
                "system_memory_usage_percent",
                MetricType.GAUGE,
                memory.percent,
                description="Memory usage percentage"
            )
            
            await self.record_metric(
                "system_memory_available_bytes",
                MetricType.GAUGE,
                memory.available,
                unit="bytes",
                description="Available memory in bytes"
            )
            
            # Disco
            disk = psutil.disk_usage('/')
            await self.record_metric(
                "system_disk_usage_percent",
                MetricType.GAUGE,
                (disk.used / disk.total) * 100,
                description="Disk usage percentage"
            )
            
            # Network
            network = psutil.net_io_counters()
            await self.record_metric(
                "system_network_bytes_sent",
                MetricType.COUNTER,
                network.bytes_sent,
                unit="bytes",
                description="Total bytes sent"
            )
            
            await self.record_metric(
                "system_network_bytes_recv",
                MetricType.COUNTER,
                network.bytes_recv,
                unit="bytes",
                description="Total bytes received"
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    async def collect_application_metrics(self):
        """Coleta métricas da aplicação"""
        try:
            # Métricas do processo atual
            process = psutil.Process()
            
            await self.record_metric(
                "app_memory_usage_bytes",
                MetricType.GAUGE,
                process.memory_info().rss,
                unit="bytes",
                description="Application memory usage"
            )
            
            await self.record_metric(
                "app_cpu_usage_percent",
                MetricType.GAUGE,
                process.cpu_percent(),
                description="Application CPU usage"
            )
            
            await self.record_metric(
                "app_open_files_count",
                MetricType.GAUGE,
                len(process.open_files()),
                description="Number of open files"
            )
            
            # Uptime
            create_time = datetime.fromtimestamp(process.create_time())
            uptime_seconds = (datetime.now() - create_time).total_seconds()
            
            await self.record_metric(
                "app_uptime_seconds",
                MetricType.GAUGE,
                uptime_seconds,
                unit="seconds",
                description="Application uptime"
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting application metrics: {e}")
    
    async def collect_business_metrics(self):
        """Coleta métricas de negócio"""
        try:
            # Simular queries para métricas de negócio
            # Em implementação real, usar repositórios
            
            # Usuários ativos
            await self.record_metric(
                "business_active_users_total",
                MetricType.GAUGE,
                150,  # Mock value
                description="Total active users"
            )
            
            # Agentes ativos
            await self.record_metric(
                "business_active_agents_total",
                MetricType.GAUGE,
                45,  # Mock value
                description="Total active agents"
            )
            
            # Tasks executadas hoje
            await self.record_metric(
                "business_tasks_completed_today",
                MetricType.COUNTER,
                1250,  # Mock value
                description="Tasks completed today"
            )
            
            # Revenue hoje
            await self.record_metric(
                "business_revenue_today_usd",
                MetricType.GAUGE,
                12450.75,  # Mock value
                unit="USD",
                description="Revenue generated today"
            )
            
            # Taxa de sucesso
            await self.record_metric(
                "business_success_rate_percent",
                MetricType.GAUGE,
                94.5,  # Mock value
                description="Overall success rate"
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting business metrics: {e}")
    
    async def collect_database_metrics(self):
        """Coleta métricas do banco de dados"""
        try:
            if not db_manager.engine:
                return
            
            pool_status = await db_manager.get_pool_status()
            
            await self.record_metric(
                "db_pool_size",
                MetricType.GAUGE,
                pool_status.get("pool_size", 0),
                description="Database pool size"
            )
            
            await self.record_metric(
                "db_pool_checked_out",
                MetricType.GAUGE,
                pool_status.get("checked_out", 0),
                description="Database connections checked out"
            )
            
            await self.record_metric(
                "db_pool_overflow",
                MetricType.GAUGE,
                pool_status.get("overflow", 0),
                description="Database pool overflow connections"
            )
            
            metrics = pool_status.get("metrics", {})
            
            await self.record_metric(
                "db_slow_queries_total",
                MetricType.COUNTER,
                metrics.get("slow_queries", 0),
                description="Total slow queries"
            )
            
            await self.record_metric(
                "db_avg_query_time_ms",
                MetricType.GAUGE,
                metrics.get("avg_query_time", 0) * 1000,
                unit="milliseconds",
                description="Average query time"
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting database metrics: {e}")
    
    async def collect_cache_metrics(self):
        """Coleta métricas do cache"""
        try:
            if not cache_manager._redis:
                return
            
            cache_metrics = await cache_manager.get_metrics()
            
            await self.record_metric(
                "cache_hit_rate_percent",
                MetricType.GAUGE,
                cache_metrics.get("hit_rate", 0),
                description="Cache hit rate"
            )
            
            await self.record_metric(
                "cache_hits_total",
                MetricType.COUNTER,
                cache_metrics.get("hits", 0),
                description="Total cache hits"
            )
            
            await self.record_metric(
                "cache_misses_total",
                MetricType.COUNTER,
                cache_metrics.get("misses", 0),
                description="Total cache misses"
            )
            
            await self.record_metric(
                "cache_errors_total",
                MetricType.COUNTER,
                cache_metrics.get("errors", 0),
                description="Total cache errors"
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting cache metrics: {e}")
    
    async def record_metric(
        self,
        name: str,
        metric_type: MetricType,
        value: float,
        labels: Dict[str, str] = None,
        unit: str = "",
        description: str = ""
    ):
        """Registra uma métrica"""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            labels=labels or {},
            unit=unit,
            description=description
        )
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append(metric)
        
        # Manter apenas métricas recentes
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.retention_period)
        self.metrics[name] = [
            m for m in self.metrics[name] 
            if m.timestamp > cutoff_time
        ]
    
    async def persist_metrics(self):
        """Persiste métricas no Redis"""
        try:
            if not cache_manager._redis:
                return
            
            # Persistir métricas atuais
            current_metrics = {}
            for name, metric_list in self.metrics.items():
                if metric_list:
                    latest_metric = metric_list[-1]
                    current_metrics[name] = {
                        "value": latest_metric.value,
                        "timestamp": latest_metric.timestamp.isoformat(),
                        "type": latest_metric.type.value,
                        "unit": latest_metric.unit,
                        "labels": latest_metric.labels
                    }
            
            await cache_manager.set(
                "metrics:current",
                current_metrics,
                ttl=self.collection_interval * 2
            )
            
            # Persistir histórico (últimas 24h)
            for name, metric_list in self.metrics.items():
                history_key = f"metrics:history:{name}"
                history_data = [
                    {
                        "value": m.value,
                        "timestamp": m.timestamp.isoformat(),
                        "labels": m.labels
                    }
                    for m in metric_list[-100:]  # Últimas 100 amostras
                ]
                
                await cache_manager.set(
                    history_key,
                    history_data,
                    ttl=self.retention_period
                )
                
        except Exception as e:
            self.logger.error(f"Error persisting metrics: {e}")
    
    def add_alert_rule(
        self,
        name: str,
        metric_name: str,
        condition: str,  # "gt", "lt", "eq"
        threshold: float,
        severity: str = "warning",
        message: str = ""
    ):
        """Adiciona regra de alerta"""
        self.alert_rules[name] = {
            "metric_name": metric_name,
            "condition": condition,
            "threshold": threshold,
            "severity": severity,
            "message": message or f"{metric_name} {condition} {threshold}"
        }
    
    async def check_alerts(self):
        """Verifica condições de alerta"""
        for alert_name, rule in self.alert_rules.items():
            try:
                metric_name = rule["metric_name"]
                
                if metric_name not in self.metrics or not self.metrics[metric_name]:
                    continue
                
                latest_metric = self.metrics[metric_name][-1]
                current_value = latest_metric.value
                threshold = rule["threshold"]
                condition = rule["condition"]
                
                alert_triggered = False
                
                if condition == "gt" and current_value > threshold:
                    alert_triggered = True
                elif condition == "lt" and current_value < threshold:
                    alert_triggered = True
                elif condition == "eq" and current_value == threshold:
                    alert_triggered = True
                
                if alert_triggered:
                    alert = Alert(
                        name=alert_name,
                        condition=f"{metric_name} {condition} {threshold}",
                        threshold=threshold,
                        current_value=current_value,
                        severity=rule["severity"],
                        message=rule["message"]
                    )
                    
                    self.alerts.append(alert)
                    await self._send_alert(alert)
                    
            except Exception as e:
                self.logger.error(f"Error checking alert {alert_name}: {e}")
    
    async def _send_alert(self, alert: Alert):
        """Envia alerta (implementar integração com sistemas externos)"""
        self.logger.warning(
            f"ALERT [{alert.severity.upper()}] {alert.name}: "
            f"{alert.message} (current: {alert.current_value}, threshold: {alert.threshold})"
        )
        
        # Aqui você pode integrar com:
        # - Slack/Discord webhooks
        # - Email notifications
        # - PagerDuty
        # - Prometheus AlertManager
        # etc.
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Retorna métricas atuais"""
        try:
            cached_metrics = await cache_manager.get("metrics:current")
            if cached_metrics:
                return cached_metrics
        except Exception:
            pass
        
        # Fallback para métricas em memória
        current_metrics = {}
        for name, metric_list in self.metrics.items():
            if metric_list:
                latest_metric = metric_list[-1]
                current_metrics[name] = {
                    "value": latest_metric.value,
                    "timestamp": latest_metric.timestamp.isoformat(),
                    "type": latest_metric.type.value,
                    "unit": latest_metric.unit
                }
        
        return current_metrics
    
    async def get_metric_history(
        self,
        metric_name: str,
        hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Retorna histórico de uma métrica"""
        try:
            history_key = f"metrics:history:{metric_name}"
            cached_history = await cache_manager.get(history_key)
            if cached_history:
                # Filtrar por período
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                return [
                    point for point in cached_history
                    if datetime.fromisoformat(point["timestamp"]) > cutoff_time
                ]
        except Exception:
            pass
        
        # Fallback para métricas em memória
        if metric_name in self.metrics:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            return [
                {
                    "value": m.value,
                    "timestamp": m.timestamp.isoformat(),
                    "labels": m.labels
                }
                for m in self.metrics[metric_name]
                if m.timestamp > cutoff_time
            ]
        
        return []
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Retorna alertas ativos"""
        return [
            {
                "name": alert.name,
                "condition": alert.condition,
                "threshold": alert.threshold,
                "current_value": alert.current_value,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved
            }
            for alert in self.alerts
            if not alert.resolved
        ]


# Instância global
metrics_collector = MetricsCollector()

# Configurar alertas padrão
async def setup_default_alerts():
    """Configura alertas padrão"""
    
    # Sistema
    metrics_collector.add_alert_rule(
        "high_cpu_usage",
        "system_cpu_usage_percent",
        "gt",
        80.0,
        "warning",
        "High CPU usage detected"
    )
    
    metrics_collector.add_alert_rule(
        "high_memory_usage",
        "system_memory_usage_percent",
        "gt",
        85.0,
        "critical",
        "High memory usage detected"
    )
    
    metrics_collector.add_alert_rule(
        "low_disk_space",
        "system_disk_usage_percent",
        "gt",
        90.0,
        "critical",
        "Low disk space detected"
    )
    
    # Cache
    metrics_collector.add_alert_rule(
        "low_cache_hit_rate",
        "cache_hit_rate_percent",
        "lt",
        70.0,
        "warning",
        "Low cache hit rate detected"
    )
    
    # Negócio
    metrics_collector.add_alert_rule(
        "low_success_rate",
        "business_success_rate_percent",
        "lt",
        90.0,
        "warning",
        "Low success rate detected"
    )
