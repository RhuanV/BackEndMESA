/**
 * MunicipalitySelector — Dropdowns dependentes estado → município (RF02).
 *
 * Controlado: pai recebe o `codigo_ibge` (7 dígitos) do município escolhido
 * via onChange. Município = '' quando o usuário ainda não selecionou.
 *
 * Carrega a lista de estados na montagem e a lista de municípios sempre que
 * o estado muda. Limpa o município selecionado quando o estado troca.
 */
import { useCallback, useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { Select } from '@/components/ui/Select';
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
    void loadStates();
  }, [loadStates]);

  useEffect(() => {
    if (!selectedUf) return;
    void loadMunicipalities(selectedUf);
  }, [selectedUf, loadMunicipalities]);

  const handleStateChange = (uf: string) => {
    setSelectedUf(uf);
    // Reset município + lista quando troca de estado (sem effect síncrono).
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
