/**
 * AssessmentMarkers — renders MESA assessments as colored pins on the map.
 *
 * Sprint 2 entregável visível: conecta o pipeline Avaliação → BD PostGIS →
 * /ranking → mapa, demonstrando o ciclo completo end-to-end. Cada sítio
 * aparece como pin colorido por score, com popup mostrando nome + nota.
 *
 * O ranking re-fetcha quando `refreshKey` muda, pra que outras telas
 * (ex.: AssessmentForm) possam disparar atualização sem precisar de
 * websockets ou polling.
 */
import { useEffect, useState } from 'react';
import maplibregl from 'maplibre-gl';
import type { RefObject } from 'react';
import { getRanking } from '@/features/results/services/rankingService';
import type { MesaRankingResult } from '@/types/mesa';
import { sanitize } from '@/lib/security/sanitize';

interface AssessmentMarkersProps {
  readonly map: RefObject<maplibregl.Map | null>;
  readonly isMapReady: boolean;
  readonly refreshKey?: number;
}

function pinColor(score: number): string {
  if (score >= 80) return '#16a34a'; // green-600
  if (score >= 60) return '#eab308'; // yellow-500
  if (score >= 40) return '#f97316'; // orange-500
  return '#dc2626'; // red-600
}

function buildPinElement(score: number): HTMLDivElement {
  const el = document.createElement('div');
  el.style.width = '28px';
  el.style.height = '28px';
  el.style.borderRadius = '50% 50% 50% 0';
  el.style.transform = 'rotate(-45deg)';
  el.style.background = pinColor(score);
  el.style.border = '2px solid white';
  el.style.boxShadow = '0 2px 6px rgba(0,0,0,0.3)';
  el.style.cursor = 'pointer';

  const inner = document.createElement('div');
  inner.style.transform = 'rotate(45deg)';
  inner.style.color = 'white';
  inner.style.fontSize = '11px';
  inner.style.fontWeight = '700';
  inner.style.textAlign = 'center';
  inner.style.lineHeight = '24px';
  inner.textContent = String(Math.round(score));
  el.appendChild(inner);
  return el;
}

function buildPopupHtml(result: MesaRankingResult): string {
  // Sanitize the only user-controlled string before injecting into innerHTML.
  const name = sanitize(result.siteName);
  const score = result.totalScore.toFixed(1);
  const lat = result.latitude.toFixed(4);
  const lng = result.longitude.toFixed(4);
  return `
    <div style="font-family: Inter, system-ui, sans-serif; padding: 4px 2px; min-width: 200px;">
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
        <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: ${pinColor(
          result.totalScore
        )};"></span>
        <strong style="font-size: 13px; color: #111827;">#${result.rank} — ${name}</strong>
      </div>
      <div style="font-size: 12px; color: #4b5563; line-height: 1.6;">
        <div><b>Score total:</b> ${score}</div>
        <div><b>Declividade:</b> ${result.slopeScore.toFixed(0)} &nbsp; <b>Distância:</b> ${result.distanceScore.toFixed(
    0
  )}</div>
        <div><b>Obstáculos:</b> ${result.obstacleScore.toFixed(0)} &nbsp; <b>Custo:</b> ${result.costScore.toFixed(
    0
  )}</div>
        <div style="font-size: 10px; color: #9ca3af; margin-top: 4px; font-family: monospace;">
          ${lat}, ${lng}
        </div>
      </div>
    </div>
  `;
}

export function AssessmentMarkers({ map, isMapReady, refreshKey = 0 }: AssessmentMarkersProps) {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isMapReady || !map.current) return;
    const mapInstance = map.current;
    let cancelled = false;
    const markers: maplibregl.Marker[] = [];

    getRanking()
      .then((results) => {
        if (cancelled) return;
        results.forEach((result) => {
          const popup = new maplibregl.Popup({ offset: 24, closeButton: true })
            .setHTML(buildPopupHtml(result));

          const marker = new maplibregl.Marker({
            element: buildPinElement(result.totalScore),
            anchor: 'bottom',
          })
            .setLngLat([result.longitude, result.latitude])
            .setPopup(popup)
            .addTo(mapInstance);

          markers.push(marker);
        });
        setError(null);
      })
      .catch(() => {
        if (!cancelled) setError('Não foi possível carregar os sítios avaliados.');
      });

    return () => {
      cancelled = true;
      markers.forEach((m) => m.remove());
    };
  }, [map, isMapReady, refreshKey]);

  if (!error) return null;
  return (
    <div className="absolute bottom-12 left-1/2 -translate-x-1/2 z-10 rounded-lg bg-danger-500/10 border border-danger-500/30 px-3 py-2 text-xs text-danger-600">
      {error}
    </div>
  );
}
