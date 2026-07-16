/**
 * useCatalogLayer — fetches a single layer's metadata from the backend catalog.
 *
 * Used by the MetadataModal to show live catalog metadata (RF01) instead of the
 * static registry. When `layerKey` is null the hook stays idle; on error it
 * exposes the message so the caller can fall back to the static registry.
 */
import { useEffect, useState } from 'react';

import { getCatalogLayer, type CatalogLayer } from '@/features/map/services/catalogApi';

interface UseCatalogLayerResult {
  readonly data: CatalogLayer | null;
  readonly isLoading: boolean;
  readonly error: string | null;
}

export function useCatalogLayer(layerKey: string | null | undefined): UseCatalogLayerResult {
  const [data, setData] = useState<CatalogLayer | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    // All state updates live in this async function (not the synchronous effect
    // body), matching the codebase pattern and the react-hooks lint rule.
    async function load() {
      if (!layerKey) {
        setData(null);
        setError(null);
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      setError(null);
      try {
        const layer = await getCatalogLayer(layerKey);
        if (!cancelled) setData(layer);
      } catch (err: unknown) {
        if (cancelled) return;
        setData(null);
        setError(err instanceof Error ? err.message : 'Erro ao carregar metadados do catálogo.');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [layerKey]);

  return { data, isLoading, error };
}
