/**
 * SecurePopup — Demonstrates secure popup rendering for MapLibre.
 *
 * SECURITY CRITICAL: MapLibre popups use raw HTML (not React rendering),
 * so they are vulnerable to XSS if properties are not sanitized.
 *
 * This module provides the function to safely display GeoJSON feature
 * properties in a MapLibre popup using DOMPurify sanitization.
 */
import maplibregl from 'maplibre-gl';
import { buildSecurePopupContent } from '@/features/map/utils/securePopupContent';

/**
 * Attaches a secure popup to the map for a clicked feature.
 *
 * All feature properties are sanitized via DOMPurify before being
 * rendered as HTML in the popup. This prevents Stored XSS attacks
 * from compromised GeoJSON data sources.
 *
 * @param map - The MapLibre map instance
 * @param coordinates - [lng, lat] where the popup should appear
 * @param properties - Raw GeoJSON feature properties (will be sanitized)
 */
export function showSecurePopup(
  map: maplibregl.Map,
  coordinates: [number, number],
  properties: Record<string, unknown>
): void {
  // SECURITY: Sanitize ALL properties before rendering
  const safeHTML = buildSecurePopupContent(properties);

  new maplibregl.Popup({
    closeButton: true,
    closeOnClick: true,
    maxWidth: '320px',
  })
    .setLngLat(coordinates)
    .setHTML(safeHTML)
    .addTo(map);
}
