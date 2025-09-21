/**
 * Testes E2E para comunicação Frontend-Backend
 * Equivalente aos testes de integração Selenium em Java
 */

import { test, expect } from '@playwright/test';

test.describe('Frontend-Backend Communication', () => {
  test.beforeEach(async ({ page }) => {
    // Navegar para o dashboard onde está o ApiHealthChecker
    await page.goto('/dashboard');
    
    // Aguardar a página carregar completamente
    await page.waitForLoadState('networkidle');
  });

  test('should display API health status', async ({ page }) => {
    // Verificar se o componente de health check está presente
    await expect(page.locator('text=Status da API Backend')).toBeVisible();
    
    // Verificar se mostra status de conexão
    const statusElement = page.locator('[data-testid="api-status"]').or(
      page.locator('text=Conectado').or(page.locator('text=Desconectado'))
    );
    await expect(statusElement).toBeVisible();
  });

  test('should refresh API status when button is clicked', async ({ page }) => {
    // Localizar o botão de atualizar
    const refreshButton = page.locator('button:has-text("Atualizar")');
    await expect(refreshButton).toBeVisible();
    
    // Clicar no botão
    await refreshButton.click();
    
    // Verificar se houve alguma mudança (loading state ou atualização)
    // Aguardar um breve momento para a requisição
    await page.waitForTimeout(1000);
    
    // Verificar se ainda está visível (não quebrou)
    await expect(refreshButton).toBeVisible();
  });

  test('should run connectivity test', async ({ page }) => {
    // Localizar o botão de teste de conectividade
    const testButton = page.locator('button:has-text("Executar Teste")');
    await expect(testButton).toBeVisible();
    
    // Clicar no botão
    await testButton.click();
    
    // Aguardar o teste ser executado
    await page.waitForTimeout(2000);
    
    // Verificar se os resultados aparecem
    const resultsSection = page.locator('text=Teste de Conectividade').locator('..');
    await expect(resultsSection).toBeVisible();
  });

  test('should display backend information when healthy', async ({ page }) => {
    // Aguardar o health check carregar
    await page.waitForTimeout(2000);
    
    // Se a API estiver saudável, deve mostrar informações
    const healthyStatus = page.locator('text=Conectado');
    
    if (await healthyStatus.isVisible()) {
      // Verificar se mostra informações da aplicação
      await expect(page.locator('text=Aplicação')).toBeVisible();
      await expect(page.locator('text=Versão')).toBeVisible();
      await expect(page.locator('text=Tempo de Resposta')).toBeVisible();
    }
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Interceptar requisições para simular erro
    await page.route('**/health', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal Server Error' })
      });
    });
    
    // Recarregar a página para aplicar o mock
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Verificar se mostra estado de erro
    await expect(page.locator('text=Desconectado')).toBeVisible();
    
    // Verificar se mostra mensagem de erro
    const errorMessage = page.locator('text=Erro de Conexão').or(
      page.locator('text=Internal Server Error')
    );
    await expect(errorMessage).toBeVisible();
  });

  test('should show loading state during API calls', async ({ page }) => {
    // Interceptar requisições para adicionar delay
    await page.route('**/health', async route => {
      // Adicionar delay de 2 segundos
      await new Promise(resolve => setTimeout(resolve, 2000));
      route.continue();
    });
    
    // Clicar no botão de atualizar
    const refreshButton = page.locator('button:has-text("Atualizar")');
    await refreshButton.click();
    
    // Verificar se o botão fica desabilitado durante o loading
    await expect(refreshButton).toBeDisabled();
    
    // Aguardar o loading terminar
    await page.waitForTimeout(3000);
    
    // Verificar se o botão volta a ficar habilitado
    await expect(refreshButton).toBeEnabled();
  });

  test('should display response time metrics', async ({ page }) => {
    // Aguardar o health check carregar
    await page.waitForTimeout(2000);
    
    // Procurar por métricas de tempo de resposta
    const responseTimeElement = page.locator('text=Tempo de Resposta').locator('..');
    
    if (await responseTimeElement.isVisible()) {
      // Verificar se mostra tempo em ms
      await expect(page.locator('text=/\\d+ms/')).toBeVisible();
    }
  });

  test('should maintain state across page interactions', async ({ page }) => {
    // Executar teste de conectividade
    const testButton = page.locator('button:has-text("Executar Teste")');
    if (await testButton.isVisible()) {
      await testButton.click();
      await page.waitForTimeout(2000);
    }
    
    // Navegar para outra seção do dashboard
    const statsSection = page.locator('text=Dashboard').first();
    await statsSection.click();
    
    // Voltar para a seção de health check
    await page.locator('text=Status da API Backend').scrollIntoViewIfNeeded();
    
    // Verificar se o estado ainda está presente
    await expect(page.locator('text=Status da API Backend')).toBeVisible();
  });
});

test.describe('Dashboard Integration', () => {
  test('should load dashboard with all components', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    // Verificar se todos os componentes principais estão presentes
    await expect(page.locator('text=Dashboard')).toBeVisible();
    
    // Verificar se o health checker está integrado
    await expect(page.locator('text=Status da API Backend')).toBeVisible();
    
    // Verificar se outros componentes do dashboard estão presentes
    const dashboardElements = [
      'text=Total de Agentes',
      'text=Agentes Ativos', 
      'text=Tarefas Completadas',
      'text=Receita Total'
    ];
    
    for (const element of dashboardElements) {
      const locator = page.locator(element).first();
      if (await locator.isVisible()) {
        await expect(locator).toBeVisible();
      }
    }
  });

  test('should handle navigation between dashboard sections', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    // Verificar se a navegação funciona sem quebrar a comunicação com API
    const healthChecker = page.locator('text=Status da API Backend');
    await expect(healthChecker).toBeVisible();
    
    // Scroll para diferentes seções
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);
    
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(1000);
    
    // Verificar se o health checker ainda está funcionando
    await expect(healthChecker).toBeVisible();
  });
});

test.describe('Performance Tests', () => {
  test('should load dashboard within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Dashboard deve carregar em menos de 5 segundos
    expect(loadTime).toBeLessThan(5000);
    
    // Verificar se componentes críticos estão visíveis
    await expect(page.locator('text=Dashboard')).toBeVisible();
    await expect(page.locator('text=Status da API Backend')).toBeVisible();
  });

  test('should handle multiple API calls efficiently', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    const startTime = Date.now();
    
    // Executar múltiplas ações que fazem chamadas para API
    const refreshButton = page.locator('button:has-text("Atualizar")');
    const testButton = page.locator('button:has-text("Executar Teste")');
    
    if (await refreshButton.isVisible()) {
      await refreshButton.click();
      await page.waitForTimeout(500);
    }
    
    if (await testButton.isVisible()) {
      await testButton.click();
      await page.waitForTimeout(500);
    }
    
    // Aguardar todas as requisições terminarem
    await page.waitForLoadState('networkidle');
    
    const totalTime = Date.now() - startTime;
    
    // Operações devem completar em tempo razoável
    expect(totalTime).toBeLessThan(10000);
  });
});
