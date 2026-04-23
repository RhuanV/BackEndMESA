/**
 * DOMPurify sanitization wrapper for GeoAvia.
 *
 * This module is the SINGLE SOURCE OF TRUTH for HTML sanitization.
 * Every dynamic string rendered in the DOM — especially GeoJSON properties
 * in map popups — MUST pass through these functions.
 *
 * Defense in Depth: Even though React escapes JSX by default, we add
 * DOMPurify as an extra layer to catch edge cases (e.g., when building
 * popup HTML strings for MapLibre, which doesn't use React's rendering).
 */
import DOMPurify from 'dompurify';

/**
 * Strict DOMPurify configuration.
 * Only allows safe formatting tags — no scripts, no event handlers, no links.
 */
const STRICT_CONFIG = {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'br', 'span'],
  ALLOWED_ATTR: ['class'],
  ALLOW_DATA_ATTR: false,
  ALLOW_UNKNOWN_PROTOCOLS: false,
  RETURN_TRUSTED_TYPE: false,
};

/**
 * Sanitizes a single string value for safe DOM insertion.
 * Strips all dangerous HTML while preserving safe formatting.
 *
 * @param dirty - The untrusted string to sanitize
 * @returns A safe string that can be rendered in the DOM
 */
export function sanitize(dirty: string): string {
  return DOMPurify.sanitize(dirty, STRICT_CONFIG) as string;
}

/**
 * Sanitizes all string values within a GeoJSON properties object.
 * Non-string values (numbers, booleans) are passed through as-is
 * since they cannot contain executable code.
 *
 * CRITICAL: This MUST be called before rendering any GeoJSON property
 * in a map popup to prevent Stored XSS from compromised geographic data.
 *
 * @param properties - Raw GeoJSON properties from an API response
 * @returns A new object with all string values sanitized
 */
export function sanitizeGeoJSONProperties(
  properties: Record<string, unknown>
): Record<string, string | number | boolean | null> {
  const sanitized: Record<string, string | number | boolean | null> = {};

  for (const [key, value] of Object.entries(properties)) {
    const safeKey = sanitize(key);

    if (typeof value === 'string') {
      sanitized[safeKey] = sanitize(value);
    } else if (typeof value === 'number' || typeof value === 'boolean') {
      sanitized[safeKey] = value;
    } else if (value === null || value === undefined) {
      sanitized[safeKey] = null;
    } else {
      // Nested objects/arrays: convert to sanitized string representation
      sanitized[safeKey] = sanitize(String(value));
    }
  }

  return sanitized;
}
