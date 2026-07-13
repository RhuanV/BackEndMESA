/**
 * ScreeningPage — Spatial screening of a candidate point (HU-29 + HU-26).
 *
 * Takes coordinates + target municipality, fires POST /screening and displays
 * the ternary result: viavel / intermediario (within buffer) / restrito.
 * Access: coordinator, manager, operator (gate on the backend).
 */
import { useState } from 'react';
import type { FormEvent } from 'react';
import { isAxiosError } from 'axios';
import { Button, Input } from '@/components/ui';
import { MunicipalitySelector } from '@/features/regions/components/MunicipalitySelector';
import {
  runScreening,
  type ScreeningResult,
  type ScreeningStatus,
} from '@/features/screening/services/screeningApi';

const LAYER_LABELS: Record<string, string> = {
  airport: 'Aeroporto',
  federal_highway: 'Rodovia federal',
  federal_highway_osm: 'Rodovia federal (OSM)',
  state_highway_osm: 'Rodovia estadual (OSM)',
  railway: 'Ferrovia',
  railway_osm: 'Ferrovia (OSM)',
  waterway: 'Hidrovia',
  waterway_osm: 'Hidrovia (OSM)',
  port: 'Porto',
  power_line: 'Linha de transmissão',
  outside_target_municipality: 'Fora do município alvo',
};

const STATUS_META: Record<
  ScreeningStatus,
  { label: string; cardClass: string; badgeClass: string }
> = {
  viavel: {
    label: 'Viável',
    cardClass: 'border-emerald-300 bg-emerald-50',
    badgeClass: 'bg-emerald-600 text-white',
  },
  intermediario: {
    label: 'Intermediário',
    cardClass: 'border-amber-300 bg-amber-50',
    badgeClass: 'bg-amber-500 text-white',
  },
  restrito: {
    label: 'Restrito',
    cardClass: 'border-rose-300 bg-rose-50',
    badgeClass: 'bg-rose-600 text-white',
  },
};

function formatLayer(code: string): string {
  return LAYER_LABELS[code] ?? code;
}

function formatDistance(meters: number): string {
  return meters >= 1000 ? `${(meters / 1000).toFixed(1)} km` : `${meters} m`;
}

export function ScreeningPage() {
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [ibgeCode, setIbgeCode] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    const lat = Number(latitude);
    const lon = Number(longitude);
    if (Number.isNaN(lat) || lat < -90 || lat > 90) {
      setError('Latitude precisa estar entre -90 e 90.');
      return;
    }
    if (Number.isNaN(lon) || lon < -180 || lon > 180) {
      setError('Longitude precisa estar entre -180 e 180.');
      return;
    }
    if (!/^[0-9]{7}$/.test(ibgeCode)) {
      setError('Código IBGE precisa ter exatamente 7 dígitos.');
      return;
    }

    setIsSubmitting(true);
    try {
      const data = await runScreening({
        latitude: lat,
        longitude: lon,
        target_municipality_ibge_code: ibgeCode,
      });
      setResult(data);
    } catch (err) {
      if (isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (typeof detail === 'string') {
          setError(detail);
        } else if (detail && typeof detail === 'object' && 'message' in detail) {
          setError(String(detail.message));
        } else {
          setError('Erro ao executar a triagem.');
        }
      } else {
        setError('Erro inesperado ao executar a triagem.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">Triagem Espacial</h2>
        <p className="mt-1 text-sm text-neutral-500">
          Classifica um ponto como viável, intermediário ou restrito com base no município alvo,
          camadas de infraestrutura e buffers de proteção (HU-26).
        </p>
      </div>

      <form
        onSubmit={(e) => void handleSubmit(e)}
        className="mb-6 grid gap-4 rounded-xl border border-neutral-200 bg-surface p-6 shadow-sm sm:grid-cols-2"
      >
        <Input
          label="Latitude"
          type="number"
          step="any"
          value={latitude}
          onChange={(e) => setLatitude(e.target.value)}
          placeholder="-23.5"
          required
        />
        <Input
          label="Longitude"
          type="number"
          step="any"
          value={longitude}
          onChange={(e) => setLongitude(e.target.value)}
          placeholder="-46.6"
          required
        />
        <div className="sm:col-span-2">
          <MunicipalitySelector
            value={ibgeCode}
            onChange={setIbgeCode}
            disabled={isSubmitting}
          />
        </div>
        <div className="sm:col-span-2">
          <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
            {isSubmitting ? 'Triando...' : 'Rodar triagem'}
          </Button>
        </div>
      </form>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600"
        >
          {error}
        </div>
      )}

      {result && <ResultCard result={result} />}
    </div>
  );
}

function ResultCard({ result }: { result: ScreeningResult }) {
  const meta = STATUS_META[result.status];

  return (
    <div className={`rounded-xl border p-6 shadow-sm ${meta.cardClass}`}>
      <div className="mb-4 flex items-center gap-3">
        <span
          className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${meta.badgeClass}`}
        >
          {meta.label}
        </span>
        <span className="text-xs text-neutral-600">
          Município {result.validation.target_municipality_ibge_code} · SRID {result.validation.srid}
        </span>
      </div>

      {result.reasons.length > 0 && (
        <section className="mb-4">
          <h3 className="mb-2 text-sm font-semibold text-neutral-900">Motivos de restrição</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
            {result.reasons.map((reason) => (
              <li key={reason}>{formatLayer(reason)}</li>
            ))}
          </ul>
        </section>
      )}

      {result.intermediate_reasons.length > 0 && (
        <section className="mb-4">
          <h3 className="mb-2 text-sm font-semibold text-neutral-900">
            Dentro de buffers de proteção
          </h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
            {result.intermediate_reasons.map((r) => (
              <li key={r.layer}>
                {formatLayer(r.layer)} <span className="text-neutral-500">— buffer de {formatDistance(r.buffer_meters)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {result.status === 'viavel' && (
        <p className="text-sm text-neutral-700">
          Ponto fora de todas as camadas restritivas e dos buffers configurados.
        </p>
      )}

      <details className="mt-4 text-xs text-neutral-600">
        <summary className="cursor-pointer select-none font-medium">Detalhes técnicos</summary>
        <p className="mt-2">Camadas verificadas: {result.validation.layers_checked.length}</p>
        <p className="mt-1">
          Buffers aplicados:{' '}
          {Object.entries(result.validation.buffers_applied_m)
            .map(([k, m]) => `${formatLayer(k)} (${formatDistance(m)})`)
            .join(', ')}
        </p>
      </details>
    </div>
  );
}
