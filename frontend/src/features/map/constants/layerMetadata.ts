/**
 * Layer metadata registry for GeoAvia.
 *
 * Contains metadata for all known geospatial data layers used in MESA analysis.
 * Data sources: IBGE, MapBiomas, CPRM, ANADEM, DNIT.
 *
 * Security: All string values from this registry must be sanitized
 * via DOMPurify before DOM rendering (Defense in Depth).
 */

/**
 * MapLibre paint properties for a vector layer. Kept loose (Record) to avoid
 * pulling the maplibre-gl type for paint specs into this constants file.
 */
export interface LayerPaint {
  readonly maplibreType: 'line' | 'fill' | 'circle';
  readonly paint: Readonly<Record<string, unknown>>;
}

export interface LayerMetadata {
  readonly id: string;
  readonly name: string;
  readonly group: 'base' | 'analysis' | 'exclusion';
  readonly source: string;
  readonly lastUpdate: string;
  readonly epsg: string;
  readonly description: string;
  readonly type: 'vector' | 'raster';
  readonly defaultVisible: boolean;
  /** Name used in the backend /layers/{name} endpoint. Omitted = no API yet. */
  readonly backendName?: string;
  /** MapLibre paint configuration. Required when backendName is set. */
  readonly paint?: LayerPaint;
  /** False = visible but disabled in UI (no backend yet). Defaults to true. */
  readonly available?: boolean;
  /**
   * Key into the backend metadata catalog (mesa_a.layer_catalog, RF01). When
   * set, the MetadataModal shows live metadata from the catalog API instead of
   * the static fields above. Visual config stays here regardless.
   */
  readonly catalogKey?: string;
}

export const LAYER_REGISTRY: readonly LayerMetadata[] = [
  // === Dados Base ===
  {
    id: 'ibge-estados',
    name: 'Limites Estaduais',
    group: 'base',
    source: 'IBGE — Malha Estadual 2025',
    lastUpdate: '2025-12-01',
    epsg: 'EPSG:4674 (SIRGAS 2000)',
    description: 'Limites administrativos dos estados brasileiros.',
    type: 'vector',
    defaultVisible: true,
    backendName: 'state_boundaries',
    catalogKey: 'estado__ibge',
    paint: {
      maplibreType: 'line',
      paint: {
        'line-color': '#2563eb',
        'line-width': 1.5,
        'line-opacity': 0.9,
      },
    },
  },
  {
    id: 'ibge-municipios',
    name: 'Limites Municipais',
    group: 'base',
    source: 'IBGE — Malha Municipal 2025',
    lastUpdate: '2025-12-01',
    epsg: 'EPSG:4674 (SIRGAS 2000)',
    description: 'Limites administrativos dos municípios brasileiros.',
    type: 'vector',
    defaultVisible: false,
    backendName: 'municipality_boundaries',
    catalogKey: 'municipio__ibge',
    paint: {
      maplibreType: 'line',
      paint: {
        'line-color': '#10b981',
        'line-width': 0.8,
        'line-opacity': 0.6,
      },
    },
  },
  {
    id: 'dnit-rodovias',
    name: 'Rodovias Federais',
    group: 'base',
    source: 'DNIT — Sistema Nacional de Viação',
    lastUpdate: '2023-06-15',
    epsg: 'EPSG:4674 (SIRGAS 2000)',
    description: 'Rede rodoviária federal e estadual do Brasil.',
    type: 'vector',
    defaultVisible: false,
    available: false,
  },
  {
    id: 'dnit-ferrovias',
    name: 'Ferrovias',
    group: 'base',
    source: 'DNIT — Sistema Nacional de Viação',
    lastUpdate: '2023-06-15',
    epsg: 'EPSG:4674 (SIRGAS 2000)',
    description: 'Rede ferroviária brasileira ativa e planejada.',
    type: 'vector',
    defaultVisible: false,
    available: false,
  },

  // === Análise MESA ===
  {
    id: 'anadem-declividade',
    name: 'Declividade (ANADEM)',
    group: 'analysis',
    source: 'ANADEM — Modelo Digital de Elevação',
    lastUpdate: '2021-01-01',
    epsg: 'EPSG:4674 (SIRGAS 2000)',
    description: 'Mapa de declividade derivado do MDE, resolução 30m. Critério classificatório MESA.',
    type: 'raster',
    defaultVisible: false,
    available: false,
  },
  {
    id: 'mapbiomas-uso-solo',
    name: 'Uso do Solo (MapBiomas)',
    group: 'analysis',
    source: 'MapBiomas — Coleção 8.0',
    lastUpdate: '2023-09-01',
    epsg: 'EPSG:4674 (SIRGAS 2000)',
    description: 'Mapeamento anual de cobertura e uso do solo do Brasil. Resolução 30m.',
    type: 'raster',
    defaultVisible: false,
    available: false,
  },
  {
    id: 'cprm-geologia',
    name: 'Geologia (CPRM)',
    group: 'analysis',
    source: 'CPRM — Serviço Geológico do Brasil',
    lastUpdate: '2022-03-01',
    epsg: 'EPSG:4674 (SIRGAS 2000)',
    description: 'Mapa geológico do Brasil com unidades litoestratigráficas.',
    type: 'vector',
    defaultVisible: false,
    available: false,
  },

  // === Áreas Excludentes ===
  {
    id: 'funai-terras-indigenas',
    name: 'Terras Indígenas',
    group: 'exclusion',
    source: 'FUNAI — Fundação Nacional dos Povos Indígenas',
    lastUpdate: '2024-01-15',
    epsg: 'EPSG:4674 (SIRGAS 2000)',
    description: 'Terras indígenas homologadas, declaradas e em estudo. Área de exclusão imediata.',
    type: 'vector',
    defaultVisible: false,
    available: false,
  },
  {
    id: 'icmbio-ucs',
    name: 'Unidades de Conservação',
    group: 'exclusion',
    source: 'ICMBio — CNUC',
    lastUpdate: '2024-02-01',
    epsg: 'EPSG:4674 (SIRGAS 2000)',
    description: 'Unidades de conservação federais, estaduais e municipais. Área de exclusão imediata.',
    type: 'vector',
    defaultVisible: false,
    available: false,
  },
] as const;

/** Get layers by group */
export function getLayersByGroup(group: LayerMetadata['group']): readonly LayerMetadata[] {
  return LAYER_REGISTRY.filter((l) => l.group === group);
}

/** Get layer metadata by ID */
export function getLayerById(id: string): LayerMetadata | undefined {
  return LAYER_REGISTRY.find((l) => l.id === id);
}
