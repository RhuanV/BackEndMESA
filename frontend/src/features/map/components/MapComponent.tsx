/**
 * MapComponent — Interactive geospatial map with MESA layer support.
 *
 * Sprint 2 enhancements:
 * - Brazil maxBounds (SIRGAS 2000 labeled)
 * - Layer panel with tree structure
 * - Metadata modal for layer info
 * - Region selector with flyTo
 * - Base map switching (BDG/Satellite/OSM)
 * - CRS indicator overlay
 * - Debug coordinate display (dev role only)
 */
import { useState, useCallback, useEffect } from 'react';
import maplibregl from 'maplibre-gl';
import { useMap } from '@/features/map/hooks/useMap';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { LayerControl } from './LayerControl';
import { LayerPanel } from './LayerPanel';
import { MetadataModal } from './MetadataModal';
import { RegionSelector } from './RegionSelector';
import { showSecurePopup } from './SecurePopup';
import { CRS_LABEL } from '@/features/map/constants/bounds';
import type { LayerMetadata } from '@/features/map/constants/layerMetadata';

const MAP_CONTAINER_ID = 'geoavia-map';

export function MapComponent() {
  const { user } = useAuth();
  const isDevUser = user?.role === 'dev';

  const [activeBaseMap, setActiveBaseMap] = useState<'bdg-mesa' | 'satellite' | 'osm'>('bdg-mesa');
  const [isLayerPanelOpen, setIsLayerPanelOpen] = useState(false);
  const [selectedLayerMeta, setSelectedLayerMeta] = useState<LayerMetadata | null>(null);
  const [showDebug, setShowDebug] = useState(false);

  const bdgMesaStyle = import.meta.env.VITE_MAPLIBRE_STYLE_URL;
  const satelliteStyle = import.meta.env.VITE_SATELLITE_STYLE_URL;
  const osmStyle = import.meta.env.VITE_OSM_STYLE_URL;

  const { map, isMapReady, setStyle, flyTo, cursorPosition } = useMap({
    containerId: MAP_CONTAINER_ID,
    styleUrl: bdgMesaStyle,
  });

  const handleBaseMapChange = useCallback(
    (layer: 'bdg-mesa' | 'satellite' | 'osm') => {
      setActiveBaseMap(layer);
      const styles = { 'bdg-mesa': bdgMesaStyle, satellite: satelliteStyle, osm: osmStyle };
      setStyle(styles[layer]);
    },
    [bdgMesaStyle, satelliteStyle, osmStyle, setStyle]
  );

  const handleRegionSelect = useCallback(
    (center: [number, number], zoom: number) => flyTo(center, zoom),
    [flyTo]
  );

  // Click handler for secure popups
  useEffect(() => {
    const mapInstance = map.current;
    if (!mapInstance || !isMapReady) return;

    const handleClick = (e: maplibregl.MapMouseEvent) => {
      const features = mapInstance.queryRenderedFeatures(e.point);
      const feature = features[0];
      if (feature?.properties) {
        showSecurePopup(
          mapInstance,
          [e.lngLat.lng, e.lngLat.lat],
          feature.properties as Record<string, unknown>
        );
      }
    };

    mapInstance.on('click', handleClick);
    return () => { mapInstance.off('click', handleClick); };
  }, [map, isMapReady]);

  return (
    <div className="relative h-full w-full">
      <div id={MAP_CONTAINER_ID} className="h-full w-full" />

      {/* Toolbar — top-left buttons */}
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <button
          onClick={() => setIsLayerPanelOpen(!isLayerPanelOpen)}
          className="rounded-lg bg-white/90 backdrop-blur-md shadow-md border border-neutral-200/50 p-2.5 text-neutral-600 hover:text-primary-600 hover:bg-white transition-all"
          aria-label="Painel de camadas"
          type="button"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.429 9.75L2.25 12l4.179 2.25m0-4.5l5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0l4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0l-5.571 3-5.571-3" />
          </svg>
        </button>
        {isDevUser && (
          <button
            onClick={() => setShowDebug(!showDebug)}
            className={`rounded-lg shadow-md border border-neutral-200/50 p-2.5 transition-all ${
              showDebug ? 'bg-accent-500 text-white' : 'bg-white/90 backdrop-blur-md text-neutral-600 hover:text-primary-600'
            }`}
            aria-label="Toggle debug mode"
            type="button"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 12.75c1.148 0 2.278.08 3.383.237 1.037.146 1.866.966 1.866 2.013 0 3.728-2.35 6.75-5.25 6.75S6.75 18.728 6.75 15c0-1.046.83-1.867 1.866-2.013A24.204 24.204 0 0112 12.75z" />
            </svg>
          </button>
        )}
      </div>

      {/* Layer Panel (slides from left) */}
      {isLayerPanelOpen && (
        <div className="absolute top-16 left-4 z-20">
          <LayerPanel
            isOpen={isLayerPanelOpen}
            onClose={() => setIsLayerPanelOpen(false)}
            onLayerInfo={setSelectedLayerMeta}
          />
        </div>
      )}

      {/* Region Selector — top-center */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 w-80 rounded-xl bg-white/90 backdrop-blur-md shadow-lg border border-neutral-200/50 p-3">
        <RegionSelector onRegionSelect={handleRegionSelect} />
      </div>

      {/* Base Map Control */}
      <LayerControl activeLayer={activeBaseMap} onLayerChange={handleBaseMapChange} />

      {/* CRS Label */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-10 rounded-md bg-black/60 px-2 py-1 text-[10px] font-mono text-white/80">
        {CRS_LABEL}
      </div>

      {/* Debug overlay (dev only) */}
      {showDebug && isDevUser && cursorPosition && (
        <div className="absolute top-4 right-16 z-10 rounded-lg bg-black/70 px-3 py-2 text-xs font-mono text-green-400 space-y-0.5">
          <div>Lng: {cursorPosition.lng.toFixed(6)}</div>
          <div>Lat: {cursorPosition.lat.toFixed(6)}</div>
        </div>
      )}

      {/* Metadata Modal */}
      <MetadataModal layer={selectedLayerMeta} onClose={() => setSelectedLayerMeta(null)} />

      {/* Loading */}
      {!isMapReady && (
        <div className="absolute inset-0 flex items-center justify-center bg-neutral-100/80 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-3 animate-pulse-subtle">
            <div className="h-10 w-10 animate-spin rounded-full border-3 border-accent-500 border-t-transparent" />
            <p className="text-sm font-medium text-neutral-600">Carregando mapa...</p>
          </div>
        </div>
      )}
    </div>
  );
}
