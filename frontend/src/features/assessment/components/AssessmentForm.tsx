/** MESA site assessment form (React Hook Form + Zod validation). */
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { assessmentSchema } from '@/features/assessment/schemas/assessmentSchema';
import type { AssessmentFormData } from '@/features/assessment/schemas/assessmentSchema';
import { useAssessment } from '@/features/assessment/hooks/useAssessment';
import { Button, Input } from '@/components/ui';

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
      widthM: 45,
      heightM: 1200,
      angleDeg: 0,
    },
    mode: 'onBlur',
  });

  // eslint-disable-next-line react-hooks/incompatible-library -- react-hook-form's watch() is not memoizable by the React Compiler
  const hasObstacles = watch('hasObstacles');

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
      {submitSuccess && (
        <div
          role="alert"
          className="animate-fade-in rounded-lg border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-700"
        >
          ✅ Avaliação enviada com sucesso!
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="animate-fade-in rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600"
        >
          {error}
        </div>
      )}

      <Input
        label="Nome do Sítio"
        placeholder="Ex: Sítio Aeroportuário Norte"
        maxLength={100}
        error={errors.siteName?.message}
        disabled={isSubmitting}
        {...register('siteName')}
      />

      <fieldset className="space-y-4 rounded-lg border border-neutral-200 p-4">
        <legend className="px-2 text-sm font-semibold text-primary-700">
          Critérios Classificatórios MESA
        </legend>

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

      <fieldset className="space-y-4 rounded-lg border border-neutral-200 p-4">
        <legend className="px-2 text-sm font-semibold text-primary-700">
          Geometria do Sítio
        </legend>
        <p className="text-xs text-neutral-500">
          Defina as dimensões da faixa de pista e sua orientação. O centróide é a coordenada acima.
        </p>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Largura (m)"
            type="number"
            placeholder="1 - 10.000"
            step="1"
            min={1}
            max={10000}
            error={errors.widthM?.message}
            disabled={isSubmitting}
            helperText="Largura da faixa em metros (padrão ANAC: 45 m)"
            {...register('widthM', { valueAsNumber: true })}
          />

          <Input
            label="Comprimento (m)"
            type="number"
            placeholder="1 - 50.000"
            step="1"
            min={1}
            max={50000}
            error={errors.heightM?.message}
            disabled={isSubmitting}
            helperText="Comprimento da pista em metros"
            {...register('heightM', { valueAsNumber: true })}
          />
        </div>

        <Input
          label="Ângulo de Orientação (°)"
          type="number"
          placeholder="0 - 359"
          step="0.1"
          min={0}
          max={359.9}
          error={errors.angleDeg?.message}
          disabled={isSubmitting}
          helperText="Graus no sentido horário a partir do Norte geográfico"
          {...register('angleDeg', { valueAsNumber: true })}
        />
      </fieldset>

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
