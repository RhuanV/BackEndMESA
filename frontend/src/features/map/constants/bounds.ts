/**
 * Geographic bounds and constants for the Brazilian territory.
 *
 * SIRGAS 2000 (EPSG:4674) is practically identical to WGS 84 (EPSG:4326)
 * for visualization purposes (sub-meter difference). MapLibre operates
 * natively in WGS 84. We label coordinates as SIRGAS 2000 for compliance
 * with SAC/ANAC standards. True reprojection is a backend responsibility.
 */
import type { LngLatBoundsLike } from 'maplibre-gl';

/** MaxBounds for MapLibre — restricts panning to Brazilian territory with padding */
export const BRAZIL_BOUNDS: LngLatBoundsLike = [
  [-73.99, -33.77], // Southwest (SW)
  [-28.84, 5.27],   // Northeast (NE)
];

/** Geographic center of Brazil. MapLibre expects [lng, lat] order. */
export const BRAZIL_CENTER: [number, number] = [-51.9253, -14.235];

/** Zoom constraints */
export const MIN_ZOOM = 3;
export const MAX_ZOOM = 18;
export const DEFAULT_ZOOM = 4;

/** CRS display label for compliance */
export const CRS_LABEL = 'SIRGAS 2000 (EPSG:4674)';

/**
 * Approximate bounding boxes for Brazilian states.
 * Used for flyTo() on region selection.
 * Format: [centerLng, centerLat, zoom]
 */
export const STATE_CENTERS: Record<string, { center: [number, number]; zoom: number }> = {
  AC: { center: [-70.47, -9.02], zoom: 7 },
  AL: { center: [-36.62, -9.57], zoom: 8 },
  AM: { center: [-64.66, -3.47], zoom: 6 },
  AP: { center: [-51.07, 1.41], zoom: 7 },
  BA: { center: [-41.70, -12.97], zoom: 6 },
  CE: { center: [-39.32, -5.20], zoom: 7 },
  DF: { center: [-47.88, -15.79], zoom: 10 },
  ES: { center: [-40.31, -19.18], zoom: 8 },
  GO: { center: [-49.64, -15.93], zoom: 7 },
  MA: { center: [-45.27, -5.08], zoom: 7 },
  MG: { center: [-44.68, -18.51], zoom: 6 },
  MS: { center: [-54.79, -20.51], zoom: 7 },
  MT: { center: [-55.91, -12.64], zoom: 6 },
  PA: { center: [-52.48, -3.79], zoom: 6 },
  PB: { center: [-36.62, -7.12], zoom: 8 },
  PE: { center: [-37.27, -8.28], zoom: 7 },
  PI: { center: [-42.28, -7.72], zoom: 7 },
  PR: { center: [-51.45, -24.89], zoom: 7 },
  RJ: { center: [-43.17, -22.91], zoom: 8 },
  RN: { center: [-36.51, -5.79], zoom: 8 },
  RO: { center: [-63.58, -10.83], zoom: 7 },
  RR: { center: [-61.39, 2.74], zoom: 7 },
  RS: { center: [-53.21, -29.68], zoom: 7 },
  SC: { center: [-49.58, -27.24], zoom: 8 },
  SE: { center: [-37.07, -10.57], zoom: 9 },
  SP: { center: [-48.55, -22.19], zoom: 7 },
  TO: { center: [-48.33, -10.18], zoom: 7 },
};
