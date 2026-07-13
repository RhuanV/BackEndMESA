/**
 * RegionSelector — Hierarchical region filter (Brasil > Estado).
 *
 * Rendered as a toggleable panel matching the LayerPanel aesthetic.
 * On state selection, triggers flyTo on the map to the selected region.
 * State data comes from a static JSON file (no network dependency).
 */
import { useState, useCallback } from 'react';
import { Select } from '@/components/ui';
import { STATE_CENTERS } from '@/features/map/constants/bounds';
import estadosData from '@/features/map/data/estados.json';

interface RegionSelectorProps {
  readonly onRegionSelect: (center: [number, number], zoom: number) => void;
  readonly onClose: () => void;
}

const REGIONS = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul'] as const;

export function RegionSelector({ onRegionSelect, onClose }: RegionSelectorProps) {
  const [selectedRegion, setSelectedRegion] = useState('');
  const [selectedState, setSelectedState] = useState('');

  const filteredStates = selectedRegion
    ? estadosData.filter((e) => e.region === selectedRegion)
    : estadosData;

  const handleRegionChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedRegion(e.target.value);
    setSelectedState('');
  }, []);

  const handleStateChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const uf = e.target.value;
      setSelectedState(uf);
      if (uf && STATE_CENTERS[uf]) {
        onRegionSelect(STATE_CENTERS[uf].center, STATE_CENTERS[uf].zoom);
      }
    },
    [onRegionSelect]
  );

  return (
    <div className="w-72 rounded-xl bg-surface/95 backdrop-blur-md shadow-xl border border-neutral-200/50 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-neutral-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-neutral-800">Região e Estado</h3>
        <button
          onClick={onClose}
          className="rounded-lg p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-600 transition-colors"
          aria-label="Fechar painel de região"
          type="button"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="p-3 space-y-2">
        <Select
          label="Região"
          value={selectedRegion}
          onChange={handleRegionChange}
          placeholder="Todas as regiões"
          options={REGIONS.map((r) => ({ value: r, label: r }))}
        />
        <Select
          label="Estado"
          value={selectedState}
          onChange={handleStateChange}
          placeholder="Selecione o estado"
          options={filteredStates.map((e) => ({ value: e.uf, label: `${e.name} (${e.uf})` }))}
        />
      </div>
    </div>
  );
}
