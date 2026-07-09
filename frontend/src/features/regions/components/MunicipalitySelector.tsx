/**
 * MunicipalitySelector — Dependent state → municipality dropdowns (RF02).
 *
 * Controlled: the parent receives the `codigo_ibge` (7 digits) of the chosen
 * municipality via onChange. Municipality = '' when the user has not selected yet.
 *
 * Loads the list of states on mount and the list of municipalities whenever
 * the state changes. Clears the selected municipality when the state changes.
 */
import { useCallback, useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { Select } from '@/components/ui';
import {
  listMunicipalitiesByState,
  listStates,
  type MunicipalityOption,
  type StateOption,
} from '@/features/regions/services/regionsApi';

interface MunicipalitySelectorProps {
  readonly value: string;
  readonly onChange: (codigoIbge: string) => void;
  readonly disabled?: boolean;
}

export function MunicipalitySelector({
  value,
  onChange,
  disabled = false,
}: MunicipalitySelectorProps) {
  const [states, setStates] = useState<StateOption[]>([]);
  const [statesError, setStatesError] = useState<string | null>(null);
  const [selectedUf, setSelectedUf] = useState('');
  const [municipalities, setMunicipalities] = useState<MunicipalityOption[]>([]);
  const [isLoadingMunicipalities, setIsLoadingMunicipalities] = useState(false);
  const [municipalitiesError, setMunicipalitiesError] = useState<string | null>(null);

  const loadStates = useCallback(async () => {
    try {
      const list = await listStates();
      setStates(list);
    } catch (err) {
      setStatesError(isAxiosError(err) ? 'Erro ao carregar estados.' : 'Erro inesperado.');
    }
  }, []);

  const loadMunicipalities = useCallback(async (uf: string) => {
    setIsLoadingMunicipalities(true);
    setMunicipalitiesError(null);
    try {
      const list = await listMunicipalitiesByState(uf);
      setMunicipalities(list);
    } catch {
      setMunicipalitiesError('Erro ao carregar municípios.');
    } finally {
      setIsLoadingMunicipalities(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- loads states on mount
    void loadStates();
  }, [loadStates]);

  useEffect(() => {
    if (!selectedUf) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reloads municipalities when the UF changes
    void loadMunicipalities(selectedUf);
  }, [selectedUf, loadMunicipalities]);

  const handleStateChange = (uf: string) => {
    setSelectedUf(uf);
    // Reset municipality + list when the state changes (no synchronous effect).
    setMunicipalities([]);
    onChange('');
  };

  const stateOptions = states.map((s) => ({
    value: s.sigla_estado,
    label: `${s.nome_estado} (${s.sigla_estado})`,
  }));

  const municipalityOptions = municipalities.map((m) => ({
    value: m.codigo_ibge,
    label: m.nome_municipio,
  }));

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Select
        label="Estado"
        options={stateOptions}
        value={selectedUf}
        onChange={(e) => handleStateChange(e.target.value)}
        placeholder="Selecione o estado"
        disabled={disabled || states.length === 0}
        error={statesError ?? undefined}
      />
      <Select
        label="Município"
        options={municipalityOptions}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={
          !selectedUf
            ? 'Escolha o estado primeiro'
            : isLoadingMunicipalities
              ? 'Carregando...'
              : 'Selecione o município'
        }
        disabled={disabled || !selectedUf || isLoadingMunicipalities}
        error={municipalitiesError ?? undefined}
      />
    </div>
  );
}
