/**
 * AbortController Hook
 * Hook para gerenciar AbortController e prevenir vazamentos de memória
 */

import { useEffect, useRef, useCallback } from 'react';

export const useAbortController = () => {
  const abortControllerRef = useRef<AbortController | null>(null);

  // Criar novo AbortController
  const createController = useCallback(() => {
    // Abortar controller anterior se existir
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Criar novo controller
    abortControllerRef.current = new AbortController();
    return abortControllerRef.current;
  }, []);

  // Obter signal do controller atual
  const getSignal = useCallback(() => {
    if (!abortControllerRef.current) {
      abortControllerRef.current = new AbortController();
    }
    return abortControllerRef.current.signal;
  }, []);

  // Abortar operações
  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  // Cleanup automático quando componente desmonta
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    createController,
    getSignal,
    abort,
    signal: getSignal(),
  };
};

// Hook para fetch com AbortController
export const useAbortableFetch = () => {
  const { createController } = useAbortController();

  const abortableFetch = useCallback(async <T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> => {
    const controller = createController();
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error: any) {
      // Não tratar AbortError como erro real
      if (error.name === 'AbortError') {
        console.log('Fetch aborted:', url);
        throw error;
      }
      
      console.error('Fetch error:', error);
      throw error;
    }
  }, [createController]);

  return { abortableFetch };
};

// Hook para intervalos com cleanup
export const useAbortableInterval = () => {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const { getSignal } = useAbortController();

  const setAbortableInterval = useCallback((
    callback: () => void | Promise<void>,
    delay: number
  ) => {
    // Limpar intervalo anterior
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    const signal = getSignal();
    
    const wrappedCallback = async () => {
      if (signal.aborted) return;
      
      try {
        await callback();
      } catch (error: any) {
        if (error.name !== 'AbortError') {
          console.error('Interval callback error:', error);
        }
      }
    };

    intervalRef.current = setInterval(wrappedCallback, delay);

    // Cleanup quando signal for abortado
    signal.addEventListener('abort', () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    });

    return intervalRef.current;
  }, [getSignal]);

  const clearAbortableInterval = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Cleanup automático
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    setAbortableInterval,
    clearAbortableInterval,
  };
};

// Hook para timeouts com cleanup
export const useAbortableTimeout = () => {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const { getSignal } = useAbortController();

  const setAbortableTimeout = useCallback((
    callback: () => void | Promise<void>,
    delay: number
  ) => {
    // Limpar timeout anterior
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    const signal = getSignal();
    
    const wrappedCallback = async () => {
      if (signal.aborted) return;
      
      try {
        await callback();
      } catch (error: any) {
        if (error.name !== 'AbortError') {
          console.error('Timeout callback error:', error);
        }
      }
    };

    timeoutRef.current = setTimeout(wrappedCallback, delay);

    // Cleanup quando signal for abortado
    signal.addEventListener('abort', () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    });

    return timeoutRef.current;
  }, [getSignal]);

  const clearAbortableTimeout = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // Cleanup automático
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    setAbortableTimeout,
    clearAbortableTimeout,
  };
};
