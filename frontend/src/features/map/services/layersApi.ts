/**
 * layersApi — Fetch GeoJSON layers from the backend.
 *
 * Calls GET /layers/{layer_name}?zoom=z1|z2|z3&bbox=west,south,east,north
 * Auth is handled by the global apiClient (Bearer token set in AuthContext).
 */
import type { FeatureCollection } from 'geojson';
import apiClient from '@/lib/api/axiosInstance';

export type ZoomLevel = 'z1' | 'z2' | 'z3';

interface FetchLayerParams {
  readonly layerName: string;
  readonly zoom: ZoomLevel;
  readonly bbox?: readonly [number, number, number, number];
}

export async function fetchLayer({
  layerName,
  zoom,
  bbox,
}: FetchLayerParams): Promise<FeatureCollection> {
  const params: Record<string, string> = { zoom };
  if (bbox) {
    params['bbox'] = bbox.join(',');
  }

  const response = await apiClient.get<FeatureCollection>(
    `/layers/${layerName}`,
    { params }
  );
  return response.data;
}

/**
 * Maps a MapLibre zoom level to one of the three resolution views.
 *
 * Thresholds were tuned against state/municipality data:
 *   < 5     → z1 (~5.5 km tolerance — Brazil-wide view)
 *   5 ≤ z < 9 → z2 (~1.1 km tolerance — state view)
 *   ≥ 9     → z3 (~220 m tolerance — municipal/local view)
 */
export function zoomLevelFor(maplibreZoom: number): ZoomLevel {
  if (maplibreZoom < 5) return 'z1';
  if (maplibreZoom < 9) return 'z2';
  return 'z3';
}
