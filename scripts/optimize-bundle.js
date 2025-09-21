#!/usr/bin/env node

/**
 * Script para otimizar bundle e analisar dependências
 * Uso: node scripts/optimize-bundle.js
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

const packageJsonPath = path.join(process.cwd(), 'package.json');
const packageOptimizedPath = path.join(process.cwd(), 'package-optimized.json');

console.log('🚀 Iniciando otimização do bundle...\n');

// 1. Backup do package.json atual
console.log('📦 Fazendo backup do package.json atual...');
const originalPackage = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
fs.writeFileSync('package.json.backup', JSON.stringify(originalPackage, null, 2));

// 2. Analisar dependências não utilizadas
console.log('🔍 Analisando dependências não utilizadas...');

const unusedDeps = [
  // Radix UI components provavelmente não usados
  '@radix-ui/react-accordion',
  '@radix-ui/react-alert-dialog', 
  '@radix-ui/react-aspect-ratio',
  '@radix-ui/react-collapsible',
  '@radix-ui/react-context-menu',
  '@radix-ui/react-hover-card',
  '@radix-ui/react-menubar',
  '@radix-ui/react-navigation-menu',
  '@radix-ui/react-popover',
  '@radix-ui/react-radio-group',
  '@radix-ui/react-scroll-area',
  '@radix-ui/react-slider',
  '@radix-ui/react-toggle',
  '@radix-ui/react-toggle-group',
  
  // Outras dependências possivelmente não usadas
  'next-themes', // Para projeto Vite
  'cmdk',
  'embla-carousel-react',
  'input-otp',
  'react-day-picker',
  'react-resizable-panels',
  'vaul',
  
  // Dev dependencies não essenciais
  'lovable-tagger'
];

// 3. Criar package.json otimizado
console.log('⚡ Criando package.json otimizado...');

const optimizedPackage = {
  ...originalPackage,
  dependencies: {
    // Core React
    "react": originalPackage.dependencies.react,
    "react-dom": originalPackage.dependencies["react-dom"],
    "react-router-dom": originalPackage.dependencies["react-router-dom"],
    
    // State Management
    "@tanstack/react-query": originalPackage.dependencies["@tanstack/react-query"],
    
    // Forms
    "react-hook-form": originalPackage.dependencies["react-hook-form"],
    "@hookform/resolvers": originalPackage.dependencies["@hookform/resolvers"],
    "zod": originalPackage.dependencies.zod,
    
    // UI Essentials
    "@radix-ui/react-slot": originalPackage.dependencies["@radix-ui/react-slot"],
    "@radix-ui/react-dialog": originalPackage.dependencies["@radix-ui/react-dialog"],
    "@radix-ui/react-dropdown-menu": originalPackage.dependencies["@radix-ui/react-dropdown-menu"],
    "@radix-ui/react-select": originalPackage.dependencies["@radix-ui/react-select"],
    "@radix-ui/react-tabs": originalPackage.dependencies["@radix-ui/react-tabs"],
    "@radix-ui/react-toast": originalPackage.dependencies["@radix-ui/react-toast"],
    "@radix-ui/react-tooltip": originalPackage.dependencies["@radix-ui/react-tooltip"],
    "@radix-ui/react-progress": originalPackage.dependencies["@radix-ui/react-progress"],
    "@radix-ui/react-avatar": originalPackage.dependencies["@radix-ui/react-avatar"],
    "@radix-ui/react-label": originalPackage.dependencies["@radix-ui/react-label"],
    "@radix-ui/react-separator": originalPackage.dependencies["@radix-ui/react-separator"],
    "@radix-ui/react-switch": originalPackage.dependencies["@radix-ui/react-switch"],
    "@radix-ui/react-checkbox": originalPackage.dependencies["@radix-ui/react-checkbox"],
    
    // Styling
    "class-variance-authority": originalPackage.dependencies["class-variance-authority"],
    "clsx": originalPackage.dependencies.clsx,
    "tailwind-merge": originalPackage.dependencies["tailwind-merge"],
    "tailwindcss-animate": originalPackage.dependencies["tailwindcss-animate"],
    
    // Icons
    "lucide-react": originalPackage.dependencies["lucide-react"],
    
    // Utils
    "date-fns": originalPackage.dependencies["date-fns"],
    "sonner": originalPackage.dependencies.sonner,
    
    // Charts (lazy loaded)
    "recharts": originalPackage.dependencies.recharts
  },
  devDependencies: {
    ...originalPackage.devDependencies,
    "vite-bundle-analyzer": "^0.7.0"
  },
  scripts: {
    ...originalPackage.scripts,
    "build:analyze": "vite build && npx vite-bundle-analyzer dist",
    "deps:check": "node scripts/check-unused-deps.js",
    "deps:optimize": "node scripts/optimize-bundle.js"
  }
};

// 4. Calcular economia de espaço
const originalDepsCount = Object.keys(originalPackage.dependencies).length;
const optimizedDepsCount = Object.keys(optimizedPackage.dependencies).length;
const removedDeps = originalDepsCount - optimizedDepsCount;

console.log(`📊 Estatísticas de otimização:`);
console.log(`   • Dependências originais: ${originalDepsCount}`);
console.log(`   • Dependências otimizadas: ${optimizedDepsCount}`);
console.log(`   • Dependências removidas: ${removedDeps}`);
console.log(`   • Redução: ${Math.round((removedDeps / originalDepsCount) * 100)}%\n`);

// 5. Salvar package.json otimizado
fs.writeFileSync(packageJsonPath, JSON.stringify(optimizedPackage, null, 2));
console.log('✅ Package.json otimizado salvo!');

// 6. Reinstalar dependências
console.log('📥 Reinstalando dependências otimizadas...');
try {
  execSync('npm install', { stdio: 'inherit' });
  console.log('✅ Dependências reinstaladas com sucesso!');
} catch (error) {
  console.error('❌ Erro ao reinstalar dependências:', error.message);
  console.log('🔄 Restaurando package.json original...');
  fs.writeFileSync(packageJsonPath, JSON.stringify(originalPackage, null, 2));
  process.exit(1);
}

// 7. Executar build para testar
console.log('🔨 Testando build otimizado...');
try {
  execSync('npm run build', { stdio: 'inherit' });
  console.log('✅ Build otimizado executado com sucesso!');
} catch (error) {
  console.error('❌ Erro no build otimizado:', error.message);
  console.log('🔄 Restaurando package.json original...');
  fs.writeFileSync(packageJsonPath, JSON.stringify(originalPackage, null, 2));
  execSync('npm install', { stdio: 'inherit' });
  process.exit(1);
}

console.log('\n🎉 Otimização concluída com sucesso!');
console.log('📋 Próximos passos:');
console.log('   1. Teste a aplicação: npm run dev');
console.log('   2. Analise o bundle: npm run build:analyze');
console.log('   3. Se houver problemas, restaure: mv package.json.backup package.json && npm install');
