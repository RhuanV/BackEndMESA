/**
 * Vite environment type declarations for GeoAvia.
 *
 * Provides strict typing for all VITE_ environment variables.
 * Every external URL must be declared here — never hardcoded in source.
 */

/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_MAPLIBRE_STYLE_URL: string;
  readonly VITE_SATELLITE_STYLE_URL: string;
  readonly VITE_OSM_STYLE_URL: string;
  readonly VITE_IBGE_WMS_URL: string;
  readonly VITE_MAPBIOMAS_WMS_URL: string;
  readonly VITE_CPRM_WMS_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
