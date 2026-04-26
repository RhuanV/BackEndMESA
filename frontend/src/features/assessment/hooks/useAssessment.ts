/**
 * useAssessment — Custom hook for MESA assessment operations.
 *
 * Manages assessment submission state and error handling.
 */
import { useState, useCallback } from 'react';
import { submitAssessment } from '@/features/assessment/services/assessmentService';
import type { AssessmentFormData } from '@/features/assessment/schemas/assessmentSchema';

export function useAssessment() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (data: AssessmentFormData) => {
    setIsSubmitting(true);
    setError(null);
    setSubmitSuccess(false);

    try {
      await submitAssessment(data);
      setSubmitSuccess(true);
    } catch (err) {
      // Security: Generic error message, never expose server details
      const message =
        err instanceof Error ? err.message : 'Erro ao enviar avaliação. Tente novamente.';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const reset = useCallback(() => {
    setSubmitSuccess(false);
    setError(null);
  }, []);

  return { submit, isSubmitting, submitSuccess, error, reset };
}
