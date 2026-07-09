/**
 * AnalysisConfigPanel — MCDA weight configuration for MESA analysis.
 *
 * Features:
 * - Weight sliders for each criterion (sum must = 100%)
 * - Slope threshold filter
 * - Transport buffer distance
 * - Exclusion zone toggle
 * - Live weight sum indicator with validation
 * - Progress bar during analysis execution
 */
import { useState, useCallback } from 'react';
import { Button, Input, ProgressBar, Slider } from '@/components/ui';
import { useAnalysis } from '@/features/analysis/hooks/useAnalysis';
import { DEFAULT_ANALYSIS_CONFIG } from '@/features/analysis/schemas/analysisSchema';
import type { AnalysisConfig } from '@/features/analysis/schemas/analysisSchema';

export function AnalysisConfigPanel() {
  const [config, setConfig] = useState<AnalysisConfig>(DEFAULT_ANALYSIS_CONFIG);
  const { submit, isProcessing, progress, status, error, reset } = useAnalysis();

  const weightSum = config.slopeWeight + config.landUseWeight + config.transportWeight + config.costWeight;
  const isWeightValid = Math.abs(weightSum - 100) < 0.01;

  const updateWeight = useCallback((field: keyof AnalysisConfig, value: number) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  }, []);

  const handleSubmit = () => {
    if (!isWeightValid) return;
    void submit(config);
  };

  return (
    <div className="space-y-6">
      {/* Weight Sum Indicator */}
      <div className={`rounded-lg px-4 py-3 text-sm font-medium ${
        isWeightValid
          ? 'bg-green-50 text-green-700 border border-green-200'
          : 'bg-danger-500/10 text-danger-600 border border-danger-500/30'
      }`}>
        Soma dos pesos: <span className="font-bold">{weightSum}%</span>
        {!isWeightValid && <span className="ml-2">(deve ser 100%)</span>}
      </div>

      {/* Weight Sliders */}
      <fieldset className="space-y-4 rounded-lg border border-neutral-200 p-4">
        <legend className="px-2 text-sm font-semibold text-primary-700">
          Pesos MCDA
        </legend>

        <Slider
          label="Declividade (ANADEM)"
          value={config.slopeWeight}
          onChange={(e) => updateWeight('slopeWeight', Number(e.target.value))}
        />
        <Slider
          label="Uso do Solo (MapBiomas)"
          value={config.landUseWeight}
          onChange={(e) => updateWeight('landUseWeight', Number(e.target.value))}
        />
        <Slider
          label="Distância Rodovias/Ferrovias"
          value={config.transportWeight}
          onChange={(e) => updateWeight('transportWeight', Number(e.target.value))}
        />
        <Slider
          label="Custo de Implantação"
          value={config.costWeight}
          onChange={(e) => updateWeight('costWeight', Number(e.target.value))}
        />
      </fieldset>

      {/* Threshold & Buffer */}
      <fieldset className="space-y-4 rounded-lg border border-neutral-200 p-4">
        <legend className="px-2 text-sm font-semibold text-primary-700">
          Parâmetros de Filtro
        </legend>

        <Slider
          label="Limiar de Declividade"
          value={config.slopeThreshold}
          min={0}
          max={45}
          step={0.5}
          unit="°"
          onChange={(e) => updateWeight('slopeThreshold', Number(e.target.value))}
        />

        <Input
          label="Buffer Rodovias/Ferrovias (km)"
          type="number"
          value={config.transportBufferKm}
          min={0}
          max={500}
          step={5}
          onChange={(e) => updateWeight('transportBufferKm', Number(e.target.value))}
        />
      </fieldset>

      {/* Exclusion Zones */}
      <div className="flex items-center gap-3 rounded-lg border border-neutral-200 p-4">
        <input
          type="checkbox"
          id="applyExclusions"
          checked={config.applyExclusions}
          onChange={(e) => setConfig((prev) => ({ ...prev, applyExclusions: e.target.checked }))}
          className="h-4 w-4 rounded border-neutral-300 text-primary-600 focus:ring-accent-500"
        />
        <label htmlFor="applyExclusions" className="text-sm font-medium text-neutral-700">
          Aplicar Áreas Excludentes
          <span className="block text-xs text-neutral-400">Terras Indígenas + Unidades de Conservação</span>
        </label>
      </div>

      {/* Progress */}
      {isProcessing && (
        <div className="animate-fade-in space-y-2">
          <ProgressBar
            value={progress}
            label={status?.status === 'processing' ? 'Processando análise...' : 'Enviando configuração...'}
          />
        </div>
      )}

      {/* Success */}
      {status?.status === 'completed' && (
        <div role="alert" className="animate-fade-in rounded-lg border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-700">
          ✅ Análise concluída! Visualize os resultados na aba Resultados.
        </div>
      )}

      {/* Error */}
      {error && (
        <div role="alert" className="animate-fade-in rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <Button
          onClick={handleSubmit}
          disabled={!isWeightValid || isProcessing}
          isLoading={isProcessing}
          className="flex-1"
          size="lg"
        >
          Calcular Índice de Adequabilidade
        </Button>
        <Button variant="ghost" onClick={reset} disabled={isProcessing} size="lg">
          Limpar
        </Button>
      </div>
    </div>
  );
}
