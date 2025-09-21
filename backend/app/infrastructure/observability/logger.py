"""
Structured Logging System
Sistema de logging estruturado com correlação de requests e métricas
"""

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps

import structlog
from pythonjsonlogger import jsonlogger


# Context variables para correlação
request_id_ctx: ContextVar[str] = ContextVar('request_id', default='')
user_id_ctx: ContextVar[str] = ContextVar('user_id', default='')
trace_id_ctx: ContextVar[str] = ContextVar('trace_id', default='')


class CorrelationFilter(logging.Filter):
    """Filtro para adicionar IDs de correlação aos logs"""
    
    def filter(self, record):
        record.request_id = request_id_ctx.get('')
        record.user_id = user_id_ctx.get('')
        record.trace_id = trace_id_ctx.get('')
        record.timestamp = datetime.utcnow().isoformat()
        return True


class CustomJSONFormatter(jsonlogger.JsonFormatter):
    """Formatter JSON customizado"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Adicionar campos padrão
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Campos de correlação
        log_record['request_id'] = getattr(record, 'request_id', '')
        log_record['user_id'] = getattr(record, 'user_id', '')
        log_record['trace_id'] = getattr(record, 'trace_id', '')
        
        # Informações do processo
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread
        
        # Adicionar stack trace para erros
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


class StructuredLogger:
    """
    Logger estruturado com correlação e métricas
    
    Funcionalidades:
    - Logging estruturado em JSON
    - Correlação de requests
    - Métricas de performance
    - Integração com sistemas externos
    - Sampling inteligente
    """
    
    def __init__(self, name: str = __name__):
        self.name = name
        self.logger = self._setup_logger()
        self._setup_structlog()
    
    def _setup_logger(self) -> logging.Logger:
        """Configura o logger padrão"""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        
        # Remover handlers existentes
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Handler para stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Formatter JSON
        formatter = CustomJSONFormatter(
            fmt='%(timestamp)s %(level)s %(name)s %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Adicionar filtro de correlação
        handler.addFilter(CorrelationFilter())
        
        logger.addHandler(handler)
        logger.propagate = False
        
        return logger
    
    def _setup_structlog(self):
        """Configura structlog"""
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    def set_correlation_id(self, request_id: str = None, user_id: str = None, trace_id: str = None):
        """Define IDs de correlação"""
        if request_id:
            request_id_ctx.set(request_id)
        if user_id:
            user_id_ctx.set(user_id)
        if trace_id:
            trace_id_ctx.set(trace_id)
    
    def info(self, message: str, **kwargs):
        """Log de informação"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de aviso"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log de erro"""
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        self.logger.debug(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log crítico"""
        self.logger.critical(message, extra=kwargs)
    
    def log_request(self, method: str, path: str, status_code: int, duration: float, **kwargs):
        """Log específico para requests HTTP"""
        self.info(
            "HTTP Request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration * 1000, 2),
            **kwargs
        )
    
    def log_database_query(self, query: str, duration: float, rows_affected: int = None, **kwargs):
        """Log específico para queries de banco"""
        self.info(
            "Database Query",
            query=query[:200] + "..." if len(query) > 200 else query,
            duration_ms=round(duration * 1000, 2),
            rows_affected=rows_affected,
            **kwargs
        )
    
    def log_cache_operation(self, operation: str, key: str, hit: bool = None, duration: float = None, **kwargs):
        """Log específico para operações de cache"""
        self.info(
            "Cache Operation",
            operation=operation,
            key=key,
            hit=hit,
            duration_ms=round(duration * 1000, 2) if duration else None,
            **kwargs
        )
    
    def log_business_event(self, event_type: str, entity_id: str, **kwargs):
        """Log específico para eventos de negócio"""
        self.info(
            "Business Event",
            event_type=event_type,
            entity_id=entity_id,
            **kwargs
        )
    
    def log_security_event(self, event_type: str, severity: str, **kwargs):
        """Log específico para eventos de segurança"""
        self.warning(
            "Security Event",
            event_type=event_type,
            severity=severity,
            **kwargs
        )
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "", **kwargs):
        """Log específico para métricas de performance"""
        self.info(
            "Performance Metric",
            metric_name=metric_name,
            value=value,
            unit=unit,
            **kwargs
        )


# Instância global
logger = StructuredLogger()


# Decorators para logging automático
def log_execution_time(func_name: str = None):
    """Decorator para logar tempo de execução"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_performance_metric(
                    metric_name=f"{name}_execution_time",
                    value=duration,
                    unit="seconds",
                    success=True
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.log_performance_metric(
                    metric_name=f"{name}_execution_time",
                    value=duration,
                    unit="seconds",
                    success=False,
                    error=str(e)
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_performance_metric(
                    metric_name=f"{name}_execution_time",
                    value=duration,
                    unit="seconds",
                    success=True
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.log_performance_metric(
                    metric_name=f"{name}_execution_time",
                    value=duration,
                    unit="seconds",
                    success=False,
                    error=str(e)
                )
                raise
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    return decorator


def log_function_calls(include_args: bool = False, include_result: bool = False):
    """Decorator para logar chamadas de função"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            
            log_data = {"function": func_name}
            if include_args:
                log_data["args"] = str(args)[:200]
                log_data["kwargs"] = {k: str(v)[:100] for k, v in kwargs.items()}
            
            logger.debug("Function called", **log_data)
            
            try:
                result = await func(*args, **kwargs)
                if include_result:
                    logger.debug(
                        "Function completed",
                        function=func_name,
                        result=str(result)[:200] if result else None
                    )
                return result
            except Exception as e:
                logger.error(
                    "Function failed",
                    function=func_name,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            
            log_data = {"function": func_name}
            if include_args:
                log_data["args"] = str(args)[:200]
                log_data["kwargs"] = {k: str(v)[:100] for k, v in kwargs.items()}
            
            logger.debug("Function called", **log_data)
            
            try:
                result = func(*args, **kwargs)
                if include_result:
                    logger.debug(
                        "Function completed",
                        function=func_name,
                        result=str(result)[:200] if result else None
                    )
                return result
            except Exception as e:
                logger.error(
                    "Function failed",
                    function=func_name,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    return decorator


# Context managers
class LogContext:
    """Context manager para logging com contexto"""
    
    def __init__(self, **context):
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.debug("Context started", **self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type:
            logger.error(
                "Context failed",
                duration_ms=round(duration * 1000, 2),
                error=str(exc_val),
                error_type=exc_type.__name__,
                **self.context
            )
        else:
            logger.debug(
                "Context completed",
                duration_ms=round(duration * 1000, 2),
                **self.context
            )


# Middleware para FastAPI
class LoggingMiddleware:
    """Middleware para logging de requests"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Gerar ID de request
        request_id = str(uuid.uuid4())
        request_id_ctx.set(request_id)
        
        start_time = time.time()
        
        # Interceptar response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                logger.log_request(
                    method=scope["method"],
                    path=scope["path"],
                    status_code=message["status"],
                    duration=duration,
                    request_id=request_id
                )
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


# Configuração para diferentes ambientes
def setup_logging(environment: str = "development", log_level: str = "INFO"):
    """Configura logging para diferentes ambientes"""
    
    level = getattr(logging, log_level.upper())
    
    if environment == "production":
        # Em produção, usar formato JSON estruturado
        logging.basicConfig(
            level=level,
            format='%(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
    elif environment == "development":
        # Em desenvolvimento, usar formato mais legível
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
    
    # Configurar níveis para bibliotecas externas
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
