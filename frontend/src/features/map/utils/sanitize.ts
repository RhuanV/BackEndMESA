/**
 * Map-specific sanitization utilities for GeoAvia.
 *
 * CRITICAL SECURITY MODULE: Sanitizes GeoJSON properties before rendering
 * in MapLibre popups. MapLibre uses raw HTML for popups (not React),
 * so DOMPurify is the last line of defense against Stored XSS from
 * compromised geographic data.
 */
import { sanitize, sanitizeGeoJSONProperties } from '@/lib/security/sanitize';

/**
 * Builds a sanitized HTML string for a MapLibre popup.
 *
 * Each GeoJSON property is sanitized individually before being
 * composed into the final HTML string. Even the property KEYS are
 * sanitized (an attacker could craft malicious key names).
 *
 * @param properties - Raw GeoJSON feature properties from API
 * @returns Safe HTML string for use in MapLibre Popup.setHTML()
 */
export function buildSecurePopupContent(
  properties: Record<string, unknown>
): string {
  const safe = sanitizeGeoJSONProperties(properties);

  const entries = Object.entries(safe)
    .filter(([, val]) => val !== null && val !== undefined)
    .map(([key, val]) => {
      const safeKey = sanitize(key);
      const safeVal = sanitize(String(val));
      return `
        <div style="display:flex;justify-content:space-between;gap:12px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.1)">
          <span style="color:#94a3b8;font-size:12px;white-space:nowrap">${safeKey}</span>
          <span style="color:#f1f5f9;font-size:12px;font-weight:500;text-align:right">${safeVal}</span>
        </div>
      `;
    })
    .join('');

  return `<div style="min-width:180px">${entries}</div>`;
}
