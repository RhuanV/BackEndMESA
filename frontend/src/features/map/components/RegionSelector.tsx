/**
 * RegionSelector — Hierarchical region filter (Brasil > Estado).
 *
 * On state selection, triggers flyTo on the map to the selected region.
 * State data comes from a static JSON file (no network dependency).
 */
import { useState, useCallback } from 'react';
import { Select } from '@/components/ui/Select';
import { STATE_CENTERS } from '@/features/map/constants/bounds';
import estadosData from '@/features/map/data/estados.json';

interface RegionSelectorProps {
  readonly onRegionSelect: (center: [number, number], zoom: number) => void;
}

const REGIONS = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul'] as const;

export function RegionSelector({ onRegionSelect }: RegionSelectorProps) {
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
    <div className="space-y-2">
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
  );
}
