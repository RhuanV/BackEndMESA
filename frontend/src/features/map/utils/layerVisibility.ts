/**
 * Persistent layer visibility utilities for GeoAvia.
 *
 * Reads and writes the user's layer toggle preferences to localStorage so
 * that both the LayerConfigPage (admin) and the MapComponent (runtime) share
 * the same source of truth without needing a React context or global store.
 */
import { LAYER_REGISTRY } from '@/features/map/constants/layerMetadata';

const STORAGE_KEY = 'geoavia:layer-visibility';

/** Returns the set of layer IDs the user has enabled, falling back to
 *  LAYER_REGISTRY defaults if nothing has been stored yet. */
export function getStoredVisibleIds(): Set<string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return new Set(JSON.parse(raw) as string[]);
  } catch {
    // Corrupt storage — fall through to defaults
  }
  return new Set(
    LAYER_REGISTRY
      .filter((l) => l.defaultVisible && l.available !== false)
      .map((l) => l.id)
  );
}

/** Persists the current set of visible layer IDs to localStorage. */
export function storeVisibleIds(ids: ReadonlySet<string>): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...ids]));
  } catch {
    // Storage full or unavailable — silently ignore
  }
}
