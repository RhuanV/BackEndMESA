/**
 * GeoJSON type definitions for GeoAvia map features.
 *
 * Security note: All GeoJSON properties from external sources MUST be
 * sanitized via DOMPurify before rendering in the DOM.
 */

/** GeoJSON properties after sanitization */
export interface SanitizedGeoJSONProperties {
  readonly [key: string]: string | number | boolean | null;
}

/** Typed GeoJSON Feature for map rendering */
export interface GeoAviaFeature {
  readonly type: 'Feature';
  readonly geometry: {
    readonly type: string;
    readonly coordinates: number[] | number[][] | number[][][];
  };
  readonly properties: SanitizedGeoJSONProperties;
}

/** GeoJSON FeatureCollection for map data */
export interface GeoAviaFeatureCollection {
  readonly type: 'FeatureCollection';
  readonly features: GeoAviaFeature[];
}
