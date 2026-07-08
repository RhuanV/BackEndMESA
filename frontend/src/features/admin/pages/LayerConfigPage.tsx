/**
 * LayerConfigPage — Admin-only global layer configuration.
 *
 * Each layer with a backend data source (backendName set) shows a "Fonte de dados"
 * dropdown: the admin can pick any user-uploaded shapefile as the fallback data
 * source for that layer. This is used when Airflow has not yet loaded data into
 * the base tables (mesa_a.vetor_limites_*).
 *
 * Toggle state is persisted in localStorage via layerVisibility utils.
 */
import { useState, useEffect } from 'react';
import { LAYER_REGISTRY } from '@/features/map/constants/layerMetadata';
import { getStoredVisibleIds, storeVisibleIds } from '@/features/map/utils/layerVisibility';
import { getLayerSource, setLayerSource } from '@/features/map/services/layersApi';
import { listShapefiles } from '@/features/data/services/shapefilesApi';
import type { UploadedLayer } from '@/features/data/services/shapefilesApi';

export function LayerConfigPage() {
  const [visibleIds, setVisibleIds] = useState<Set<string>>(getStoredVisibleIds);
  const [uploads, setUploads] = useState<UploadedLayer[]>([]);
  // Map layer backendName → upload_id (null = no fallback configured)
  const [sources, setSources] = useState<Record<string, number | null>>({});
  const [savingSource, setSavingSource] = useState<string | null>(null);

  // Load all uploads and current source mappings once on mount
  useEffect(() => {
    void listShapefiles().then(setUploads).catch(() => {});

    const layersWithBackend = LAYER_REGISTRY.filter((l) => l.backendName);
    Promise.all(
      layersWithBackend.map((l) =>
        getLayerSource(l.backendName!)
          .then((s) => ({ name: l.backendName!, upload_id: s.upload_id }))
          .catch(() => ({ name: l.backendName!, upload_id: null }))
      )
    ).then((results) => {
      setSources(Object.fromEntries(results.map((r) => [r.name, r.upload_id])));
    });
  }, []);

  const toggle = (id: string) => {
    setVisibleIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      storeVisibleIds(next);
      return next;
    });
  };

  const handleSourceChange = async (backendName: string, value: string) => {
    const uploadId = value === '' ? null : Number(value);
    setSavingSource(backendName);
    try {
      await setLayerSource(backendName, uploadId);
      setSources((prev) => ({ ...prev, [backendName]: uploadId }));
    } catch {
      // Silently ignore — user can retry
    } finally {
      setSavingSource(null);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">Configuração de Camadas</h2>
        <p className="mt-1 text-sm text-neutral-500">
          Ative ou desative camadas globais. Para camadas sem dados do Airflow, vincule um
          shapefile importado como fonte alternativa.
        </p>
      </div>

      <div className="space-y-3">
        {LAYER_REGISTRY.map((layer) => {
          const isDisabled = layer.available === false;
          const isVisible = visibleIds.has(layer.id);
          const currentUploadId = layer.backendName ? sources[layer.backendName] : undefined;
          const isSaving = layer.backendName === savingSource;

          return (
            <div
              key={layer.id}
              className={`rounded-xl border border-neutral-200 bg-white shadow-sm hover:shadow-md transition-shadow ${isDisabled ? 'opacity-60' : ''}`}
            >
              {/* Main row */}
              <div className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <span className={`inline-flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold ${
                    layer.type === 'raster' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
                  }`}>
                    {layer.type === 'raster' ? 'R' : 'V'}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-neutral-900">{layer.name}</p>
                    <p className="text-xs text-neutral-400">{layer.source}</p>
                    {isDisabled && (
                      <p className="text-[10px] text-neutral-400 italic">Indisponível — dados não carregados</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                    layer.group === 'exclusion' ? 'bg-red-100 text-red-700'
                    : layer.group === 'analysis' ? 'bg-teal-100 text-teal-700'
                    : 'bg-neutral-100 text-neutral-600'
                  }`}>
                    {layer.group}
                  </span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isVisible}
                      disabled={isDisabled}
                      onChange={() => toggle(layer.id)}
                      className="sr-only peer"
                      aria-label={`Camada ${layer.name}: ${isVisible ? 'visível' : 'oculta'}`}
                    />
                    <div className="w-9 h-5 bg-neutral-300 peer-focus:ring-2 peer-focus:ring-accent-500 rounded-full peer peer-checked:bg-primary-600 transition-colors after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-full peer-disabled:cursor-not-allowed" />
                  </label>
                </div>
              </div>

              {/* Source selector (only for layers with a backend endpoint) */}
              {layer.backendName && (
                <div className="border-t border-neutral-100 px-4 py-3 flex items-center gap-3">
                  <span className="text-[11px] text-neutral-500 whitespace-nowrap">Fonte de dados:</span>
                  <select
                    value={currentUploadId ?? ''}
                    onChange={(e) => void handleSourceChange(layer.backendName!, e.target.value)}
                    disabled={isSaving}
                    className="flex-1 rounded-lg border border-neutral-200 bg-neutral-50 px-2 py-1 text-xs text-neutral-700 focus:outline-none focus:ring-2 focus:ring-accent-500 disabled:opacity-50"
                    aria-label={`Fonte de dados para ${layer.name}`}
                  >
                    <option value="">Airflow (automático)</option>
                    {uploads.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.layer_name} ({u.feature_count} feat.)
                      </option>
                    ))}
                  </select>
                  {isSaving && (
                    <span className="text-[10px] text-neutral-400">Salvando…</span>
                  )}
                  {!isSaving && currentUploadId != null && (
                    <span className="text-[10px] text-emerald-600">✓ Vinculado</span>
                  )}
                  {!isSaving && currentUploadId == null && (
                    <span className="text-[10px] text-amber-500">Sem dados</span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
