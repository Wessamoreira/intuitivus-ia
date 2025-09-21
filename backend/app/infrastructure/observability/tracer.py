"""
Distributed Tracing System
Sistema de tracing distribuído com OpenTelemetry
"""

import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional, List
from functools import wraps

from opentelemetry import trace, baggage
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.trace.status import Status, StatusCode

from .logger import logger


class DistributedTracer:
    """
    Sistema de tracing distribuído
    
    Funcionalidades:
    - Tracing de requests HTTP
    - Tracing de queries de banco
    - Tracing de operações de cache
    - Tracing de chamadas externas
    - Correlação com logs
    - Métricas de performance
    """
    
    def __init__(self, service_name: str = "intuitivus-flow", jaeger_endpoint: str = None):
        self.service_name = service_name
        self.jaeger_endpoint = jaeger_endpoint or "http://localhost:14268/api/traces"
        self.tracer = None
        self._setup_tracing()
    
    def _setup_tracing(self):
        """Configura o sistema de tracing"""
        
        # Configurar resource
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": "1.0.0",
            "deployment.environment": "production"
        })
        
        # Configurar provider
        trace.set_tracer_provider(TracerProvider(resource=resource))
        
        # Configurar exporter Jaeger
        jaeger_exporter = JaegerExporter(
            endpoint=self.jaeger_endpoint,
        )
        
        # Configurar processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        # Obter tracer
        self.tracer = trace.get_tracer(__name__)
        
        # Instrumentar bibliotecas automaticamente
        self._setup_auto_instrumentation()
    
    def _setup_auto_instrumentation(self):
        """Configura instrumentação automática"""
        
        # FastAPI
        FastAPIInstrumentor.instrument()
        
        # SQLAlchemy
        SQLAlchemyInstrumentor.instrument()
        
        # Redis
        RedisInstrumentor.instrument()
        
        # Requests HTTP
        RequestsInstrumentor.instrument()
    
    @contextmanager
    def start_span(self, name: str, attributes: Dict[str, Any] = None, parent_context=None):
        """Inicia um novo span"""
        
        with self.tracer.start_as_current_span(
            name,
            context=parent_context,
            attributes=attributes or {}
        ) as span:
            
            # Adicionar informações básicas
            span.set_attribute("service.name", self.service_name)
            span.set_attribute("span.start_time", time.time())
            
            try:
                yield span
            except Exception as e:
                # Marcar span como erro
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                raise
            finally:
                span.set_attribute("span.end_time", time.time())
    
    def trace_http_request(self, method: str, url: str, status_code: int = None, 
                          user_id: str = None, **attributes):
        """Traça request HTTP"""
        
        span_name = f"HTTP {method} {url}"
        
        with self.start_span(span_name) as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", url)
            span.set_attribute("http.scheme", "https")
            
            if status_code:
                span.set_attribute("http.status_code", status_code)
                
                # Marcar como erro se status >= 400
                if status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR, f"HTTP {status_code}"))
            
            if user_id:
                span.set_attribute("user.id", user_id)
            
            # Adicionar atributos customizados
            for key, value in attributes.items():
                span.set_attribute(key, value)
            
            return span
    
    def trace_database_query(self, query: str, table: str = None, operation: str = None, 
                           rows_affected: int = None, **attributes):
        """Traça query de banco de dados"""
        
        span_name = f"DB {operation or 'query'}"
        if table:
            span_name += f" {table}"
        
        with self.start_span(span_name) as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.statement", query[:500])  # Limitar tamanho
            
            if table:
                span.set_attribute("db.table", table)
            
            if operation:
                span.set_attribute("db.operation", operation)
            
            if rows_affected is not None:
                span.set_attribute("db.rows_affected", rows_affected)
            
            # Adicionar atributos customizados
            for key, value in attributes.items():
                span.set_attribute(key, value)
            
            return span
    
    def trace_cache_operation(self, operation: str, key: str, hit: bool = None, 
                            ttl: int = None, **attributes):
        """Traça operação de cache"""
        
        span_name = f"Cache {operation}"
        
        with self.start_span(span_name) as span:
            span.set_attribute("cache.system", "redis")
            span.set_attribute("cache.operation", operation)
            span.set_attribute("cache.key", key)
            
            if hit is not None:
                span.set_attribute("cache.hit", hit)
            
            if ttl is not None:
                span.set_attribute("cache.ttl", ttl)
            
            # Adicionar atributos customizados
            for key, value in attributes.items():
                span.set_attribute(key, value)
            
            return span
    
    def trace_external_call(self, service: str, method: str, endpoint: str, 
                          status_code: int = None, **attributes):
        """Traça chamada para serviço externo"""
        
        span_name = f"External {service} {method}"
        
        with self.start_span(span_name) as span:
            span.set_attribute("external.service", service)
            span.set_attribute("external.method", method)
            span.set_attribute("external.endpoint", endpoint)
            
            if status_code:
                span.set_attribute("external.status_code", status_code)
                
                if status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR, f"External call failed: {status_code}"))
            
            # Adicionar atributos customizados
            for key, value in attributes.items():
                span.set_attribute(key, value)
            
            return span
    
    def trace_business_operation(self, operation: str, entity_type: str = None, 
                               entity_id: str = None, **attributes):
        """Traça operação de negócio"""
        
        span_name = f"Business {operation}"
        if entity_type:
            span_name += f" {entity_type}"
        
        with self.start_span(span_name) as span:
            span.set_attribute("business.operation", operation)
            
            if entity_type:
                span.set_attribute("business.entity_type", entity_type)
            
            if entity_id:
                span.set_attribute("business.entity_id", entity_id)
            
            # Adicionar atributos customizados
            for key, value in attributes.items():
                span.set_attribute(key, value)
            
            return span
    
    def add_baggage(self, key: str, value: str):
        """Adiciona baggage para propagação de contexto"""
        baggage.set_baggage(key, value)
    
    def get_baggage(self, key: str) -> Optional[str]:
        """Obtém baggage do contexto"""
        return baggage.get_baggage(key)
    
    def get_current_trace_id(self) -> Optional[str]:
        """Obtém o trace ID atual"""
        current_span = trace.get_current_span()
        if current_span and current_span.get_span_context().is_valid:
            return format(current_span.get_span_context().trace_id, '032x')
        return None
    
    def get_current_span_id(self) -> Optional[str]:
        """Obtém o span ID atual"""
        current_span = trace.get_current_span()
        if current_span and current_span.get_span_context().is_valid:
            return format(current_span.get_span_context().span_id, '016x')
        return None


# Instância global
tracer = DistributedTracer()


# Decorators para tracing automático
def trace_function(operation_name: str = None, include_args: bool = False):
    """Decorator para traçar execução de função"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            
            attributes = {}
            if include_args:
                attributes["function.args"] = str(args)[:200]
                attributes["function.kwargs"] = str(kwargs)[:200]
            
            with tracer.start_span(name, attributes) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("function.success", False)
                    span.set_attribute("function.error", str(e))
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            
            attributes = {}
            if include_args:
                attributes["function.args"] = str(args)[:200]
                attributes["function.kwargs"] = str(kwargs)[:200]
            
            with tracer.start_span(name, attributes) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("function.success", False)
                    span.set_attribute("function.error", str(e))
                    raise
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    
    return decorator


def trace_database_operation(table: str = None, operation: str = None):
    """Decorator específico para operações de banco"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            
            with tracer.trace_database_operation(
                query=f"{op_name} operation",
                table=table,
                operation=op_name
            ):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            
            with tracer.trace_database_operation(
                query=f"{op_name} operation",
                table=table,
                operation=op_name
            ):
                return func(*args, **kwargs)
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    
    return decorator


def trace_cache_operation(operation: str = None):
    """Decorator específico para operações de cache"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            key = kwargs.get('key', args[0] if args else 'unknown')
            
            with tracer.trace_cache_operation(
                operation=op_name,
                key=str(key)
            ):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            key = kwargs.get('key', args[0] if args else 'unknown')
            
            with tracer.trace_cache_operation(
                operation=op_name,
                key=str(key)
            ):
                return func(*args, **kwargs)
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    
    return decorator


# Context manager para tracing manual
class TraceContext:
    """Context manager para tracing manual"""
    
    def __init__(self, operation_name: str, **attributes):
        self.operation_name = operation_name
        self.attributes = attributes
        self.span = None
    
    def __enter__(self):
        self.span = tracer.start_span(self.operation_name, self.attributes).__enter__()
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            self.span.__exit__(exc_type, exc_val, exc_tb)


# Integração com logging
def correlate_trace_with_logs():
    """Correlaciona traces com logs"""
    trace_id = tracer.get_current_trace_id()
    span_id = tracer.get_current_span_id()
    
    if trace_id:
        logger.set_correlation_id(trace_id=trace_id)
    
    return trace_id, span_id


# Middleware para FastAPI
class TracingMiddleware:
    """Middleware para tracing automático de requests"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        method = scope["method"]
        path = scope["path"]
        
        with tracer.trace_http_request(method, path) as span:
            # Adicionar informações do request
            if "user" in scope:
                span.set_attribute("user.id", scope["user"].get("id"))
            
            # Correlacionar com logs
            correlate_trace_with_logs()
            
            # Interceptar response
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    span.set_attribute("http.status_code", message["status"])
                await send(message)
            
            await self.app(scope, receive, send_wrapper)


# Configuração para diferentes ambientes
def setup_tracing(
    service_name: str = "intuitivus-flow",
    jaeger_endpoint: str = None,
    sample_rate: float = 1.0
):
    """Configura tracing para diferentes ambientes"""
    
    global tracer
    tracer = DistributedTracer(service_name, jaeger_endpoint)
    
    # Configurar sampling
    if sample_rate < 1.0:
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
        trace.get_tracer_provider().resource = trace.get_tracer_provider().resource.merge(
            Resource.create({"sampler": TraceIdRatioBased(sample_rate)})
        )
    
    logger.info(f"Tracing configurado para {service_name}", 
                jaeger_endpoint=jaeger_endpoint, 
                sample_rate=sample_rate)
