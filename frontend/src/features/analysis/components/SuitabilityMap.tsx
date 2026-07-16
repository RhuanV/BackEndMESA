/**
 * SuitabilityMap — MapLibre overlay of the MCDA suitability result (Fase 5).
 *
 * Renders the colorized suitability raster (fetched authenticated as a PNG) as a
 * georeferenced image overlay over an OSM basemap, plus the top-ranked candidate
 * points, fit to the município bounds. Self-contained: creates and disposes its
 * own map, and revokes the object URL on cleanup.
 */
import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import type { StyleSpecification } from 'maplibre-gl';

import { extractErrorDetail } from '@/lib/api/errors';
import {
  getSuitabilityMeta,
  getSuitabilityPngUrl,
} from '@/features/analysis/services/analysisService';
import type { AnalysisConfig } from '@/features/analysis/schemas/analysisSchema';

const OSM_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
      maxzoom: 19,
    },
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
};

interface SuitabilityMapProps {
  readonly config: AnalysisConfig;
}

export function SuitabilityMap({ config }: SuitabilityMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let map: maplibregl.Map | null = null;
    let objectUrl: string | null = null;
    let cancelled = false;

    async function build() {
      setLoading(true);
      setError(null);
      try {
        const [meta, pngUrl] = await Promise.all([
          getSuitabilityMeta(config),
          getSuitabilityPngUrl(config),
        ]);
        if (cancelled || !containerRef.current) {
          URL.revokeObjectURL(pngUrl);
          return;
        }
        objectUrl = pngUrl;
        const [minx, miny, maxx, maxy] = meta.bounds;

        map = new maplibregl.Map({
          container: containerRef.current,
          style: OSM_STYLE,
          bounds: [
            [minx, miny],
            [maxx, maxy],
          ],
          fitBoundsOptions: { padding: 24 },
          attributionControl: {},
        });
        map.addControl(new maplibregl.NavigationControl(), 'top-right');

        map.on('load', () => {
          if (!map) return;
          map.addSource('suitability', {
            type: 'image',
            url: pngUrl,
            // Corners: top-left, top-right, bottom-right, bottom-left.
            coordinates: [
              [minx, maxy],
              [maxx, maxy],
              [maxx, miny],
              [minx, miny],
            ],
          });
          map.addLayer({
            id: 'suitability',
            type: 'raster',
            source: 'suitability',
            paint: { 'raster-opacity': 0.7 },
          });

          map.addSource('ranked', {
            type: 'geojson',
            data: {
              type: 'FeatureCollection',
              features: meta.ranked.map((p) => ({
                type: 'Feature',
                geometry: { type: 'Point', coordinates: [p.longitude, p.latitude] },
                properties: { rank: p.rank, score: p.total_score },
              })),
            },
          });
          map.addLayer({
            id: 'ranked',
            type: 'circle',
            source: 'ranked',
            paint: {
              'circle-radius': 6,
              'circle-color': '#111827',
              'circle-stroke-color': '#ffffff',
              'circle-stroke-width': 2,
            },
          });
        });
      } catch (err) {
        if (!cancelled) setError(extractErrorDetail(err) ?? 'Erro ao carregar o mapa de adequabilidade.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void build();
    return () => {
      cancelled = true;
      if (map) map.remove();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [config]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-neutral-900">Mapa de Adequabilidade (MCDA)</h3>
        <span className="text-xs text-neutral-400">
          verde = mais adequado · áreas excluídas ficam transparentes
        </span>
      </div>
      {error && (
        <div role="alert" className="rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600">
          {error}
        </div>
      )}
      <div className="relative h-80 w-full overflow-hidden rounded-lg border border-neutral-200">
        <div ref={containerRef} className="absolute inset-0" />
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/60">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
          </div>
        )}
      </div>
    </div>
  );
}
