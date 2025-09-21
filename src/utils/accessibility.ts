/**
 * Accessibility Utilities
 * Utilitários para melhorar acessibilidade e testes
 */

// Tipos para data-testid
export type TestId = 
  // Autenticação
  | 'login-form'
  | 'login-email-input'
  | 'login-password-input'
  | 'login-submit-button'
  | 'login-toggle-password'
  | 'register-form'
  | 'register-email-input'
  | 'register-password-input'
  | 'register-confirm-password-input'
  | 'register-license-input'
  | 'register-submit-button'
  
  // Dashboard
  | 'dashboard-header'
  | 'dashboard-stats-grid'
  | 'dashboard-agents-section'
  | 'dashboard-tasks-section'
  | 'dashboard-refresh-button'
  
  // Agentes
  | 'agent-card'
  | 'agent-name'
  | 'agent-status'
  | 'agent-actions'
  | 'agent-edit-button'
  | 'agent-delete-button'
  | 'agent-toggle-status'
  | 'create-agent-button'
  | 'agents-filter'
  | 'agents-search'
  
  // Tarefas
  | 'task-item'
  | 'task-title'
  | 'task-status'
  | 'task-priority'
  | 'task-actions'
  | 'tasks-filter'
  | 'tasks-search'
  
  // Navegação
  | 'sidebar'
  | 'sidebar-toggle'
  | 'nav-dashboard'
  | 'nav-agents'
  | 'nav-tasks'
  | 'nav-campaigns'
  | 'nav-settings'
  | 'nav-logout'
  
  // Modais
  | 'modal-overlay'
  | 'modal-content'
  | 'modal-close'
  | 'modal-confirm'
  | 'modal-cancel'
  
  // Formulários
  | 'form-field'
  | 'form-label'
  | 'form-input'
  | 'form-error'
  | 'form-submit'
  | 'form-cancel'
  
  // Loading e estados
  | 'loading-spinner'
  | 'error-message'
  | 'success-message'
  | 'empty-state';

// Função para gerar data-testid consistente
export const testId = (id: TestId, suffix?: string): string => {
  return suffix ? `${id}-${suffix}` : id;
};

// Props para componentes com acessibilidade
export interface AccessibilityProps {
  'data-testid'?: TestId | string;
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  'aria-expanded'?: boolean;
  'aria-hidden'?: boolean;
  'aria-disabled'?: boolean;
  'aria-selected'?: boolean;
  'aria-checked'?: boolean;
  'aria-current'?: boolean | 'page' | 'step' | 'location' | 'date' | 'time';
  role?: string;
  tabIndex?: number;
}

// Hook para gerenciar foco
export const useFocusManagement = () => {
  const focusElement = (selector: string) => {
    const element = document.querySelector(selector) as HTMLElement;
    if (element) {
      element.focus();
    }
  };

  const focusFirstError = () => {
    const firstError = document.querySelector('[aria-invalid="true"]') as HTMLElement;
    if (firstError) {
      firstError.focus();
    }
  };

  const trapFocus = (containerSelector: string) => {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    };

    document.addEventListener('keydown', handleTabKey);
    firstElement?.focus();

    return () => {
      document.removeEventListener('keydown', handleTabKey);
    };
  };

  return {
    focusElement,
    focusFirstError,
    trapFocus,
  };
};

// Utilitários para ARIA
export const ariaUtils = {
  // Gerar IDs únicos para aria-labelledby e aria-describedby
  generateId: (prefix: string): string => {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
  },

  // Anunciar mudanças para screen readers
  announce: (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const announcer = document.createElement('div');
    announcer.setAttribute('aria-live', priority);
    announcer.setAttribute('aria-atomic', 'true');
    announcer.setAttribute('class', 'sr-only');
    announcer.textContent = message;
    
    document.body.appendChild(announcer);
    
    setTimeout(() => {
      document.body.removeChild(announcer);
    }, 1000);
  },

  // Verificar se elemento está visível para screen readers
  isVisible: (element: HTMLElement): boolean => {
    return !element.hasAttribute('aria-hidden') || 
           element.getAttribute('aria-hidden') !== 'true';
  },
};

// Validações de acessibilidade
export const a11yValidation = {
  // Verificar se botão tem label acessível
  validateButton: (element: HTMLButtonElement): string[] => {
    const issues: string[] = [];
    
    if (!element.textContent?.trim() && 
        !element.getAttribute('aria-label') && 
        !element.getAttribute('aria-labelledby')) {
      issues.push('Button must have accessible text');
    }
    
    return issues;
  },

  // Verificar se input tem label
  validateInput: (element: HTMLInputElement): string[] => {
    const issues: string[] = [];
    
    if (!element.getAttribute('aria-label') && 
        !element.getAttribute('aria-labelledby') &&
        !document.querySelector(`label[for="${element.id}"]`)) {
      issues.push('Input must have associated label');
    }
    
    return issues;
  },

  // Verificar contraste de cores (simplificado)
  validateContrast: (foreground: string, background: string): boolean => {
    // Implementação simplificada - em produção usar biblioteca específica
    return true; // Placeholder
  },
};

// Componente para texto apenas para screen readers
export const ScreenReaderOnly: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <span className="sr-only">{children}</span>
);

// Hook para detectar preferências de acessibilidade
export const useAccessibilityPreferences = () => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
  const prefersColorScheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  
  return {
    prefersReducedMotion,
    prefersHighContrast,
    prefersColorScheme,
  };
};

// Constantes para roles ARIA comuns
export const ARIA_ROLES = {
  BUTTON: 'button',
  LINK: 'link',
  MENU: 'menu',
  MENUITEM: 'menuitem',
  DIALOG: 'dialog',
  ALERT: 'alert',
  STATUS: 'status',
  REGION: 'region',
  BANNER: 'banner',
  MAIN: 'main',
  NAVIGATION: 'navigation',
  COMPLEMENTARY: 'complementary',
  CONTENTINFO: 'contentinfo',
  SEARCH: 'search',
  FORM: 'form',
  GRID: 'grid',
  GRIDCELL: 'gridcell',
  TAB: 'tab',
  TABPANEL: 'tabpanel',
  TABLIST: 'tablist',
} as const;

// Constantes para estados ARIA
export const ARIA_STATES = {
  EXPANDED: 'aria-expanded',
  SELECTED: 'aria-selected',
  CHECKED: 'aria-checked',
  DISABLED: 'aria-disabled',
  HIDDEN: 'aria-hidden',
  INVALID: 'aria-invalid',
  REQUIRED: 'aria-required',
  READONLY: 'aria-readonly',
  CURRENT: 'aria-current',
} as const;
