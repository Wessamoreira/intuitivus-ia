/**
 * Error Boundary Component
 * Componente para capturar e tratar erros em componentes React
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, RefreshCw, Bug, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Atualiza o state para mostrar a UI de erro
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log do erro
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });

    // Callback personalizado para logging
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Enviar erro para serviço de monitoramento (se configurado)
    this.reportError(error, errorInfo);
  }

  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    // Aqui você pode integrar com serviços como Sentry, LogRocket, etc.
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      errorId: this.state.errorId,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    // Exemplo de envio para API de logging
    try {
      fetch('/api/v1/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorReport),
      }).catch(() => {
        // Falha silenciosa no logging
      });
    } catch {
      // Falha silenciosa no logging
    }
  };

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = '/dashboard';
  };

  render() {
    if (this.state.hasError) {
      // Fallback personalizado
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // UI de erro padrão
      return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
          <Card className="w-full max-w-2xl">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <CardTitle className="text-xl font-semibold text-gray-900">
                Oops! Algo deu errado
              </CardTitle>
              <CardDescription className="text-gray-600">
                Ocorreu um erro inesperado na aplicação. Nossa equipe foi notificada automaticamente.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <Alert>
                <Bug className="h-4 w-4" />
                <AlertTitle>ID do Erro</AlertTitle>
                <AlertDescription className="font-mono text-sm">
                  {this.state.errorId}
                </AlertDescription>
              </Alert>

              {this.props.showDetails && this.state.error && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Detalhes Técnicos</AlertTitle>
                  <AlertDescription>
                    <div className="mt-2 space-y-2">
                      <div>
                        <strong>Erro:</strong> {this.state.error.message}
                      </div>
                      {this.state.error.stack && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-sm font-medium">
                            Stack Trace
                          </summary>
                          <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto max-h-40">
                            {this.state.error.stack}
                          </pre>
                        </details>
                      )}
                    </div>
                  </AlertDescription>
                </Alert>
              )}

              <div className="flex flex-col sm:flex-row gap-3 pt-4">
                <Button 
                  onClick={this.handleRetry}
                  className="flex items-center space-x-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>Tentar Novamente</span>
                </Button>

                <Button 
                  variant="outline"
                  onClick={this.handleReload}
                  className="flex items-center space-x-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>Recarregar Página</span>
                </Button>

                <Button 
                  variant="outline"
                  onClick={this.handleGoHome}
                  className="flex items-center space-x-2"
                >
                  <Home className="h-4 w-4" />
                  <span>Ir para Dashboard</span>
                </Button>
              </div>

              <div className="text-center text-sm text-gray-500 pt-4 border-t">
                <p>
                  Se o problema persistir, entre em contato com o suporte técnico 
                  informando o ID do erro acima.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// HOC para envolver componentes com error boundary
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
};

// Error boundary específico para seções
export const SectionErrorBoundary: React.FC<{ 
  children: ReactNode; 
  sectionName: string;
}> = ({ children, sectionName }) => (
  <ErrorBoundary
    fallback={
      <Card className="border-red-200 bg-red-50">
        <CardContent className="p-6 text-center">
          <AlertTriangle className="h-8 w-8 text-red-600 mx-auto mb-2" />
          <p className="text-red-800 font-medium">
            Erro ao carregar {sectionName}
          </p>
          <p className="text-red-600 text-sm mt-1">
            Tente recarregar a página
          </p>
        </CardContent>
      </Card>
    }
    onError={(error, errorInfo) => {
      console.error(`Error in ${sectionName}:`, error, errorInfo);
    }}
  >
    {children}
  </ErrorBoundary>
);

// Hook para capturar erros em hooks
export const useErrorHandler = () => {
  const handleError = (error: Error, context?: string) => {
    console.error(`Error${context ? ` in ${context}` : ''}:`, error);
    
    // Aqui você pode integrar com serviços de logging
    const errorReport = {
      message: error.message,
      stack: error.stack,
      context,
      timestamp: new Date().toISOString(),
      url: window.location.href,
    };

    // Enviar para API de logging
    fetch('/api/v1/errors', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(errorReport),
    }).catch(() => {
      // Falha silenciosa
    });
  };

  return { handleError };
};
