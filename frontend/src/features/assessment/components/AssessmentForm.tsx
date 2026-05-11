/**
 * AssessmentForm — MESA site assessment form.
 *
 * Integrates React Hook Form with Zod validation for the MESA classificatory
 * criteria from the Manual de Apoio 2021.
 *
 * Security:
 * - All fields validated by strict Zod schema (type, bounds, regex)
 * - Prevents XSS payloads, negative values, and payload overload
 * - Error messages are user-friendly (Portuguese)
 * - No sensitive data exposed in the DOM
 */
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { assessmentSchema } from '@/features/assessment/schemas/assessmentSchema';
import type { AssessmentFormData } from '@/features/assessment/schemas/assessmentSchema';
import { useAssessment } from '@/features/assessment/hooks/useAssessment';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export function AssessmentForm() {
  const { submit, isSubmitting, submitSuccess, error, reset } = useAssessment();

  const {
    register,
    handleSubmit,
    watch,
    reset: resetForm,
    formState: { errors },
  } = useForm<AssessmentFormData>({
    resolver: zodResolver(assessmentSchema),
    defaultValues: {
      siteName: '',
      averageSlope: 0,
      urbanCenterDistance: 0,
      hasObstacles: false,
      obstacleDescription: '',
      estimatedCost: 0,
      latitude: 0,
      longitude: 0,
    },
    mode: 'onBlur',
  });

  const hasObstacles = watch('hasObstacles');

  // Reset form after successful submission
  useEffect(() => {
    if (submitSuccess) {
      resetForm();
      const timer = setTimeout(() => reset(), 5000);
      return () => clearTimeout(timer);
    }
  }, [submitSuccess, resetForm, reset]);

  const onSubmit = (data: AssessmentFormData) => {
    void submit(data);
  };

  return (
    <form
      onSubmit={(e) => void handleSubmit(onSubmit)(e)}
      className="space-y-6"
      noValidate
      aria-label="Formulário de avaliação MESA"
    >
      {/* Success message */}
      {submitSuccess && (
        <div
          role="alert"
          className="animate-fade-in rounded-lg border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-700"
        >
          ✅ Avaliação enviada com sucesso!
        </div>
      )}

      {/* Server error */}
      {error && (
        <div
          role="alert"
          className="animate-fade-in rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600"
        >
          {error}
        </div>
      )}

      {/* Site Name */}
      <Input
        label="Nome do Sítio"
        placeholder="Ex: Sítio Aeroportuário Norte"
        maxLength={100}
        error={errors.siteName?.message}
        disabled={isSubmitting}
        {...register('siteName')}
      />

      {/* Classificatory Criteria Section */}
      <fieldset className="space-y-4 rounded-lg border border-neutral-200 p-4">
        <legend className="px-2 text-sm font-semibold text-primary-700">
          Critérios Classificatórios MESA
        </legend>

        {/* Average Slope */}
        <Input
          label="Declividade Média (%)"
          type="number"
          placeholder="0 - 100"
          step="0.01"
          min={0}
          max={100}
          error={errors.averageSlope?.message}
          disabled={isSubmitting}
          helperText="Percentual de declividade do terreno"
          {...register('averageSlope', { valueAsNumber: true })}
        />

        {/* Urban Center Distance */}
        <Input
          label="Distância de Centros Urbanos (km)"
          type="number"
          placeholder="0 - 10.000"
          step="0.1"
          min={0}
          max={10000}
          error={errors.urbanCenterDistance?.message}
          disabled={isSubmitting}
          helperText="Distância em quilômetros até o centro urbano mais próximo"
          {...register('urbanCenterDistance', { valueAsNumber: true })}
        />

        {/* Obstacles */}
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="hasObstacles"
              className="h-4 w-4 rounded border-neutral-300 text-primary-600 focus:ring-accent-500"
              disabled={isSubmitting}
              {...register('hasObstacles')}
            />
            <label htmlFor="hasObstacles" className="text-sm font-medium text-neutral-700">
              Presença de Obstáculos
            </label>
          </div>

          {hasObstacles && (
            <div className="animate-fade-in ml-7">
              <Input
                label="Descrição dos Obstáculos"
                placeholder="Descreva os obstáculos identificados"
                maxLength={500}
                error={errors.obstacleDescription?.message}
                disabled={isSubmitting}
                {...register('obstacleDescription')}
              />
            </div>
          )}
        </div>

        {/* Estimated Cost */}
        <Input
          label="Custo Estimado (R$)"
          type="number"
          placeholder="0"
          step="0.01"
          min={0}
          error={errors.estimatedCost?.message}
          disabled={isSubmitting}
          helperText="Custo estimado em Reais para implantação"
          {...register('estimatedCost', { valueAsNumber: true })}
        />
      </fieldset>

      {/* Geographic Coordinates */}
      <fieldset className="space-y-4 rounded-lg border border-neutral-200 p-4">
        <legend className="px-2 text-sm font-semibold text-primary-700">
          Coordenadas Geográficas
        </legend>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Latitude"
            type="number"
            placeholder="-90 a 90"
            step="0.000001"
            min={-90}
            max={90}
            error={errors.latitude?.message}
            disabled={isSubmitting}
            {...register('latitude', { valueAsNumber: true })}
          />

          <Input
            label="Longitude"
            type="number"
            placeholder="-180 a 180"
            step="0.000001"
            min={-180}
            max={180}
            error={errors.longitude?.message}
            disabled={isSubmitting}
            {...register('longitude', { valueAsNumber: true })}
          />
        </div>
      </fieldset>

      {/* Submit */}
      <Button
        type="submit"
        isLoading={isSubmitting}
        disabled={isSubmitting}
        className="w-full"
        size="lg"
      >
        Enviar Avaliação
      </Button>
    </form>
  );
}
