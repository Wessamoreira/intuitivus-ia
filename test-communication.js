/**
 * Teste direto de comunicação Frontend-Backend
 * Sem frameworks complexos - apenas Node.js puro
 */

import http from 'http';

console.log('🧪 TESTANDO COMUNICAÇÃO FRONTEND-BACKEND\n');

// Função para fazer requisição HTTP
function makeRequest(options) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          data: data
        });
      });
    });
    
    req.on('error', (err) => {
      reject(err);
    });
    
    req.setTimeout(5000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
    
    req.end();
  });
}

// Teste 1: Health Check
async function testHealthCheck() {
  console.log('1️⃣ Testando Health Check...');
  
  try {
    const response = await makeRequest({
      hostname: 'localhost',
      port: 8000,
      path: '/health',
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log(`   ✅ Status: ${response.statusCode}`);
    
    const data = JSON.parse(response.data);
    console.log(`   ✅ App: ${data.app_name}`);
    console.log(`   ✅ Version: ${data.version}`);
    console.log(`   ✅ Status: ${data.status}`);
    console.log(`   ✅ Message: ${data.message}`);
    
    return true;
  } catch (error) {
    console.log(`   ❌ Erro: ${error.message}`);
    return false;
  }
}

// Teste 2: API Endpoints
async function testApiEndpoints() {
  console.log('\n2️⃣ Testando Endpoints da API...');
  
  const endpoints = [
    '/api/v1/users',
    '/api/v1/agents', 
    '/api/v1/tasks',
    '/api/v1/campaigns'
  ];
  
  let successCount = 0;
  
  for (const endpoint of endpoints) {
    try {
      const response = await makeRequest({
        hostname: 'localhost',
        port: 8000,
        path: endpoint,
        method: 'GET'
      });
      
      if (response.statusCode === 200) {
        const data = JSON.parse(response.data);
        console.log(`   ✅ ${endpoint}: ${data.total || 0} items`);
        successCount++;
      } else {
        console.log(`   ❌ ${endpoint}: Status ${response.statusCode}`);
      }
    } catch (error) {
      console.log(`   ❌ ${endpoint}: ${error.message}`);
    }
  }
  
  return successCount === endpoints.length;
}

// Teste 3: CORS Headers
async function testCorsHeaders() {
  console.log('\n3️⃣ Testando Headers CORS...');
  
  try {
    const response = await makeRequest({
      hostname: 'localhost',
      port: 8000,
      path: '/health',
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:5173',
        'Access-Control-Request-Method': 'GET'
      }
    });
    
    const corsHeader = response.headers['access-control-allow-origin'];
    
    if (corsHeader === '*' || corsHeader === 'http://localhost:5173') {
      console.log(`   ✅ CORS configurado: ${corsHeader}`);
      return true;
    } else {
      console.log(`   ⚠️  CORS: ${corsHeader || 'não configurado'}`);
      return false;
    }
  } catch (error) {
    console.log(`   ❌ Erro CORS: ${error.message}`);
    return false;
  }
}

// Teste 4: Performance
async function testPerformance() {
  console.log('\n4️⃣ Testando Performance...');
  
  const times = [];
  
  for (let i = 0; i < 5; i++) {
    const start = Date.now();
    
    try {
      await makeRequest({
        hostname: 'localhost',
        port: 8000,
        path: '/health',
        method: 'GET'
      });
      
      const time = Date.now() - start;
      times.push(time);
    } catch (error) {
      console.log(`   ❌ Erro na requisição ${i + 1}: ${error.message}`);
      return false;
    }
  }
  
  const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
  const maxTime = Math.max(...times);
  const minTime = Math.min(...times);
  
  console.log(`   ✅ Tempo médio: ${avgTime.toFixed(2)}ms`);
  console.log(`   ✅ Tempo mínimo: ${minTime}ms`);
  console.log(`   ✅ Tempo máximo: ${maxTime}ms`);
  
  return avgTime < 1000; // Menos de 1 segundo
}

// Executar todos os testes
async function runAllTests() {
  console.log('🚀 INICIANDO TESTES DE COMUNICAÇÃO\n');
  
  const results = {
    healthCheck: await testHealthCheck(),
    apiEndpoints: await testApiEndpoints(),
    corsHeaders: await testCorsHeaders(),
    performance: await testPerformance()
  };
  
  console.log('\n📊 RESUMO DOS RESULTADOS:');
  console.log('================================');
  
  Object.entries(results).forEach(([test, passed]) => {
    const status = passed ? '✅ PASSOU' : '❌ FALHOU';
    const testName = test.replace(/([A-Z])/g, ' $1').toLowerCase();
    console.log(`${status} - ${testName}`);
  });
  
  const totalPassed = Object.values(results).filter(Boolean).length;
  const totalTests = Object.keys(results).length;
  
  console.log('================================');
  console.log(`📈 RESULTADO FINAL: ${totalPassed}/${totalTests} testes passaram`);
  
  if (totalPassed === totalTests) {
    console.log('🎉 COMUNICAÇÃO FRONTEND-BACKEND FUNCIONANDO PERFEITAMENTE!');
  } else {
    console.log('⚠️  ALGUNS PROBLEMAS ENCONTRADOS - VERIFICAR CONFIGURAÇÕES');
  }
  
  return totalPassed === totalTests;
}

// Executar
runAllTests().catch(console.error);
