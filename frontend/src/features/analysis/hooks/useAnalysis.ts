/**
 * useAnalysis — Hook for MESA analysis lifecycle.
 *
 * Manages: submission, progress polling with exponential backoff,
 * result storage, and error handling.
 */
import { useState, useCallback, useRef } from 'react';
import {
  submitAnalysis,
  getAnalysisStatus,
} from '@/features/analysis/services/analysisService';
import type { AnalysisStatusResponse } from '@/features/analysis/services/analysisService';
import type { AnalysisConfig } from '@/features/analysis/schemas/analysisSchema';

export function useAnalysis() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<AnalysisStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearTimeout(pollingRef.current);
      pollingRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const pollStatus = useCallback(
    async (id: string, interval: number) => {
      try {
        const result = await getAnalysisStatus(id);
        setStatus(result);
        setProgress(result.progress);

        if (result.status === 'completed' || result.status === 'failed') {
          stopPolling();
          if (result.status === 'failed') {
            setError(result.error ?? 'Processamento falhou. Tente novamente.');
          }
          return;
        }

        // Exponential backoff: 1s → 2s → 4s → 8s, max 8s
        const nextInterval = Math.min(interval * 2, 8000);
        pollingRef.current = setTimeout(() => {
          void pollStatus(id, nextInterval);
        }, nextInterval);
      } catch {
        setError('Erro ao verificar status do processamento.');
        stopPolling();
      }
    },
    [stopPolling]
  );

  const submit = useCallback(
    async (config: AnalysisConfig) => {
      setIsSubmitting(true);
      setError(null);
      setProgress(0);
      setStatus(null);

      try {
        const { id } = await submitAnalysis(config);
        setIsSubmitting(false);
        setIsPolling(true);
        void pollStatus(id, 1000); // Start polling at 1s
      } catch {
        setError('Erro ao enviar configuração de análise.');
        setIsSubmitting(false);
      }
    },
    [pollStatus]
  );

  const reset = useCallback(() => {
    stopPolling();
    setProgress(0);
    setStatus(null);
    setError(null);
  }, [stopPolling]);

  return {
    submit,
    reset,
    isSubmitting,
    isPolling,
    progress,
    status,
    error,
    isProcessing: isSubmitting || isPolling,
  };
}
