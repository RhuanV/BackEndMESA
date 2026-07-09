/**
 * Renders MESA assessment sites as score-coloured polygons (MapLibre
 * GeoJSON source + fill/line/symbol layers).
 *
 * Score colour bands: ≥80 green (#16a34a), ≥60 yellow (#eab308),
 * ≥40 orange (#f97316), <40 red (#dc2626).
 */
import { useEffect, useState } from 'react';
import maplibregl from 'maplibre-gl';
import type { RefObject } from 'react';
import type { FeatureCollection, Feature, Geometry } from 'geojson';
import { getRanking } from '@/features/results/services/rankingService';

const SOURCE_ID = 'assessment-polygons';
const FILL_LAYER  = 'assessment-fill';
const LINE_LAYER  = 'assessment-line';
const LABEL_LAYER = 'assessment-label';

interface AssessmentMarkersProps {
  readonly map: RefObject<maplibregl.Map | null>;
  readonly isMapReady: boolean;
  readonly refreshKey?: number;
}

export function AssessmentMarkers({ map, isMapReady, refreshKey = 0 }: AssessmentMarkersProps) {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const m = map.current;
    if (!isMapReady || !m) return;

    let cancelled = false;

    getRanking()
      .then((results) => {
        if (cancelled) return;

        const features: Feature[] = results
          .filter((r) => r.geometry)
          .map((r) => {
            const geom = JSON.parse(r.geometry) as Geometry;
            return {
              type: 'Feature',
              geometry: geom,
              properties: {
                rank: r.rank,
                siteName: r.siteName,
                totalScore: r.totalScore,
                slopeScore: r.slopeScore,
                distanceScore: r.distanceScore,
                obstacleScore: r.obstacleScore,
                costScore: r.costScore,
                // Colour expression uses this property via a MapLibre match expression
                scoreColor:
                  r.totalScore >= 80 ? '#16a34a'
                  : r.totalScore >= 60 ? '#eab308'
                  : r.totalScore >= 40 ? '#f97316'
                  : '#dc2626',
                labelText: String(Math.round(r.totalScore)),
              },
            };
          });

        const geojson: FeatureCollection = { type: 'FeatureCollection', features };

        const existing = m.getSource(SOURCE_ID);
        if (existing) {
          (existing as maplibregl.GeoJSONSource).setData(geojson);
        } else {
          m.addSource(SOURCE_ID, { type: 'geojson', data: geojson });

          m.addLayer({
            id: FILL_LAYER,
            type: 'fill',
            source: SOURCE_ID,
            paint: {
              'fill-color': ['get', 'scoreColor'],
              'fill-opacity': 0.35,
            },
          });

          m.addLayer({
            id: LINE_LAYER,
            type: 'line',
            source: SOURCE_ID,
            paint: {
              'line-color': ['get', 'scoreColor'],
              'line-width': 2,
            },
          });

          m.addLayer({
            id: LABEL_LAYER,
            type: 'symbol',
            source: SOURCE_ID,
            layout: {
              'text-field': ['get', 'labelText'],
              'text-size': 13,
              'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
              'text-allow-overlap': true,
              'text-ignore-placement': true,
            },
            paint: {
              'text-color': '#ffffff',
              'text-halo-color': ['get', 'scoreColor'],
              'text-halo-width': 2,
            },
          });
        }

        m.on('click', FILL_LAYER, (e) => {
          const props = e.features?.[0]?.properties;
          if (!props) return;
          new maplibregl.Popup({ closeButton: true, offset: 4 })
            .setLngLat(e.lngLat)
            .setHTML(`
              <div style="font-family:Inter,system-ui,sans-serif;padding:4px 2px;min-width:200px">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                  <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${String(props['scoreColor'])};"></span>
                  <strong style="font-size:13px;color:#111827">#${String(props['rank'])} — ${String(props['siteName'])}</strong>
                </div>
                <div style="font-size:12px;color:#4b5563;line-height:1.6">
                  <div><b>Score total:</b> ${Number(props['totalScore']).toFixed(1)}</div>
                  <div><b>Declividade:</b> ${Number(props['slopeScore']).toFixed(0)} &nbsp; <b>Distância:</b> ${Number(props['distanceScore']).toFixed(0)}</div>
                  <div><b>Obstáculos:</b> ${Number(props['obstacleScore']).toFixed(0)} &nbsp; <b>Custo:</b> ${Number(props['costScore']).toFixed(0)}</div>
                </div>
              </div>`)
            .addTo(m);
        });

        m.on('mouseenter', FILL_LAYER, () => { m.getCanvas().style.cursor = 'pointer'; });
        m.on('mouseleave', FILL_LAYER, () => { m.getCanvas().style.cursor = ''; });

        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError('Não foi possível carregar os sítios avaliados.');
      });

    return () => {
      cancelled = true;
      // Layers and source intentionally persist across re-renders; they are updated
      // via setData() on the next run. We re-read map.current (not the captured `m`):
      // when the map is destroyed the ref becomes null and we must not touch a removed map.
      // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional re-read: null signals a removed map
      const live = map.current;
      if (!live) return;
      [LABEL_LAYER, LINE_LAYER, FILL_LAYER].forEach((id) => {
        if (live.getLayer(id)) live.removeLayer(id);
      });
      if (live.getSource(SOURCE_ID)) live.removeSource(SOURCE_ID);
    };
  }, [map, isMapReady, refreshKey]);

  if (!error) return null;
  return (
    <div className="absolute bottom-12 left-1/2 -translate-x-1/2 z-10 rounded-lg bg-danger-500/10 border border-danger-500/30 px-3 py-2 text-xs text-danger-600">
      {error}
    </div>
  );
}
