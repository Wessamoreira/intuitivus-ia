/**
 * Componente para verificar saúde da API e comunicação Frontend-Backend
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useApiHealth, useConnectivityTest } from '@/hooks/useApiHealth';
import { RefreshCw, CheckCircle, XCircle, Clock, Server } from 'lucide-react';

export const ApiHealthChecker: React.FC = () => {
  const { healthStatus, isLoading, refetch } = useApiHealth();
  const { testResults, runConnectivityTest } = useConnectivityTest();

  const getStatusColor = (isHealthy: boolean) => {
    return isHealthy ? 'bg-green-500' : 'bg-red-500';
  };

  const getStatusIcon = (isHealthy: boolean) => {
    return isHealthy ? (
      <CheckCircle className="w-4 h-4 text-green-500" />
    ) : (
      <XCircle className="w-4 h-4 text-red-500" />
    );
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            Status da API Backend
          </CardTitle>
          <CardDescription>
            Verificação em tempo real da comunicação frontend-backend
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Status Principal */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon(healthStatus.isHealthy)}
              <span className="font-medium">
                {healthStatus.isHealthy ? 'Conectado' : 'Desconectado'}
              </span>
              <Badge 
                variant={healthStatus.isHealthy ? 'default' : 'destructive'}
                className={getStatusColor(healthStatus.isHealthy)}
              >
                {healthStatus.status}
              </Badge>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>
          </div>

          {/* Detalhes da API */}
          {healthStatus.isHealthy && (
            <div className="grid grid-cols-2 gap-4 p-4 bg-green-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-600">Aplicação</p>
                <p className="text-sm">{healthStatus.app_name || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Versão</p>
                <p className="text-sm">{healthStatus.version || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Tempo de Resposta</p>
                <p className="text-sm flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {healthStatus.responseTime}ms
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">URL Base</p>
                <p className="text-sm">http://localhost:8000</p>
              </div>
            </div>
          )}

          {/* Erro */}
          {healthStatus.error && (
            <div className="p-4 bg-red-50 rounded-lg">
              <p className="text-sm font-medium text-red-800">Erro de Conexão</p>
              <p className="text-sm text-red-600 mt-1">{healthStatus.error}</p>
            </div>
          )}

          {/* Teste de Conectividade */}
          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium">Teste de Conectividade</h4>
              <Button
                variant="outline"
                size="sm"
                onClick={runConnectivityTest}
              >
                Executar Teste
              </Button>
            </div>
            
            {testResults.lastTest && (
              <div className="grid grid-cols-3 gap-4 p-3 bg-gray-50 rounded-lg text-sm">
                <div>
                  <p className="font-medium text-gray-600">Status Backend</p>
                  <div className="flex items-center gap-1 mt-1">
                    {getStatusIcon(testResults.backend)}
                    <span>{testResults.backend ? 'OK' : 'Falha'}</span>
                  </div>
                </div>
                <div>
                  <p className="font-medium text-gray-600">Tempo de Resposta</p>
                  <p className="mt-1">{testResults.responseTime}ms</p>
                </div>
                <div>
                  <p className="font-medium text-gray-600">Último Teste</p>
                  <p className="mt-1">{testResults.lastTest.toLocaleTimeString()}</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
