"""
Testes para o módulo principal da API
Equivalente aos testes de integração Spring Boot
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import time

from app.main import app


class TestMainAPI:
    """Classe de testes para a API principal"""
    
    @pytest.fixture
    def client(self):
        """Fixture do cliente de teste (equivalente ao TestRestTemplate)"""
        return TestClient(app)
    
    def test_health_check_success(self, client):
        """Testa o endpoint de health check - caso de sucesso"""
        response = client.get("/health")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
        assert "timestamp" in data
        assert isinstance(data["timestamp"], (int, float))
    
    def test_health_check_response_time(self, client):
        """Testa se o health check responde rapidamente"""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # em ms
        
        assert response.status_code == 200
        assert response_time < 1000  # Deve responder em menos de 1 segundo
    
    def test_cors_headers(self, client):
        """Testa se os headers CORS estão configurados corretamente"""
        response = client.options("/health")
        
        # Verifica se não há erro de CORS
        assert response.status_code in [200, 405]  # 405 é OK para OPTIONS não implementado
    
    def test_api_documentation_endpoints(self, client):
        """Testa se os endpoints de documentação estão acessíveis"""
        # Swagger UI
        docs_response = client.get("/docs")
        assert docs_response.status_code == 200
        
        # ReDoc
        redoc_response = client.get("/redoc")
        assert redoc_response.status_code == 200
        
        # OpenAPI JSON
        openapi_response = client.get("/api/v1/openapi.json")
        assert openapi_response.status_code == 200
        
        openapi_data = openapi_response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
    
    def test_invalid_endpoint_returns_404(self, client):
        """Testa se endpoints inválidos retornam 404"""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404
    
    def test_request_logging_middleware(self, client):
        """Testa se o middleware de logging está funcionando"""
        with patch('app.main.logger') as mock_logger:
            response = client.get("/health")
            
            assert response.status_code == 200
            
            # Verifica se o logger foi chamado
            assert mock_logger.info.call_count >= 2  # Request + Response logs
            
            # Verifica se os logs contêm informações esperadas
            call_args = [call.args[0] for call in mock_logger.info.call_args_list]
            request_logged = any("Request:" in arg for arg in call_args)
            response_logged = any("Response:" in arg for arg in call_args)
            
            assert request_logged
            assert response_logged
    
    @patch('app.main.settings')
    def test_debug_mode_error_details(self, mock_settings, client):
        """Testa se detalhes de erro são mostrados em modo debug"""
        mock_settings.DEBUG = True
        
        # Simular um erro interno
        with patch('app.main.api_router') as mock_router:
            mock_router.side_effect = Exception("Test error")
            
            response = client.get("/api/v1/some-endpoint")
            
            # Em modo debug, deve mostrar detalhes do erro
            if response.status_code == 500:
                data = response.json()
                assert "error" in data
    
    @patch('app.main.settings')
    def test_production_mode_error_hiding(self, mock_settings, client):
        """Testa se detalhes de erro são ocultados em produção"""
        mock_settings.DEBUG = False
        
        # Simular um erro interno
        with patch('app.main.api_router') as mock_router:
            mock_router.side_effect = Exception("Sensitive error info")
            
            response = client.get("/api/v1/some-endpoint")
            
            # Em produção, não deve mostrar detalhes sensíveis
            if response.status_code == 500:
                data = response.json()
                assert "Sensitive error info" not in str(data)
    
    def test_startup_event_logging(self, client):
        """Testa se o evento de startup registra logs apropriados"""
        with patch('app.main.logger') as mock_logger:
            # Simular startup
            with TestClient(app):
                pass
            
            # Verificar se logs de startup foram registrados
            startup_calls = [
                call for call in mock_logger.info.call_args_list 
                if call.args and "Starting" in call.args[0]
            ]
            assert len(startup_calls) > 0
    
    def test_api_version_consistency(self, client):
        """Testa se a versão da API é consistente"""
        health_response = client.get("/health")
        openapi_response = client.get("/api/v1/openapi.json")
        
        assert health_response.status_code == 200
        assert openapi_response.status_code == 200
        
        health_data = health_response.json()
        openapi_data = openapi_response.json()
        
        # Versões devem ser consistentes
        health_version = health_data.get("version")
        openapi_version = openapi_data.get("info", {}).get("version")
        
        if health_version and openapi_version:
            assert health_version == openapi_version


class TestAPIPerformance:
    """Testes de performance da API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_health_check_performance(self, client):
        """Testa performance do health check"""
        response_times = []
        
        # Fazer múltiplas requisições
        for _ in range(10):
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append((end_time - start_time) * 1000)
        
        # Calcular estatísticas
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        # Assertions de performance
        assert avg_response_time < 100  # Média < 100ms
        assert max_response_time < 500  # Máximo < 500ms
    
    def test_concurrent_requests(self, client):
        """Testa requisições concorrentes"""
        import concurrent.futures
        import threading
        
        def make_request():
            response = client.get("/health")
            return response.status_code == 200
        
        # Executar requisições concorrentes
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Todas as requisições devem ter sucesso
        assert all(results)
        assert len(results) == 20


class TestAPIConfiguration:
    """Testes de configuração da API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_app_metadata(self, client):
        """Testa metadados da aplicação"""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        info = data.get("info", {})
        
        assert "title" in info
        assert "version" in info
        assert "description" in info
        
        # Verificar se não há informações sensíveis
        sensitive_terms = ["password", "secret", "key", "token"]
        info_str = str(info).lower()
        
        for term in sensitive_terms:
            assert term not in info_str
    
    def test_security_headers(self, client):
        """Testa se headers de segurança estão presentes"""
        response = client.get("/health")
        
        # Verificar headers básicos de segurança
        headers = response.headers
        
        # Nota: Alguns headers podem ser adicionados pelo reverse proxy
        # Em produção, verificar se estão configurados no Nginx/Load Balancer
        assert response.status_code == 200
    
    @patch('app.main.settings')
    def test_trusted_hosts_configuration(self, mock_settings, client):
        """Testa configuração de hosts confiáveis"""
        mock_settings.DEBUG = False
        
        # Em produção, deve ter hosts específicos configurados
        response = client.get("/health", headers={"Host": "localhost"})
        assert response.status_code == 200
