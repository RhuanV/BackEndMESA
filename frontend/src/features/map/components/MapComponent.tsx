/** Interactive geospatial map: MESA vector layers + user-uploaded shapefiles. */
import { useState, useCallback, useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import { useMap } from '@/features/map/hooks/useMap';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { AssessmentMarkers } from './AssessmentMarkers';
import { LayerControl } from './LayerControl';
import { LayerPanel } from './LayerPanel';
import { MetadataModal } from './MetadataModal';
import { RegionSelector } from './RegionSelector';
import { showSecurePopup } from './SecurePopup';
import { CRS_LABEL } from '@/features/map/constants/bounds';
import { LAYER_REGISTRY } from '@/features/map/constants/layerMetadata';
import type { LayerMetadata } from '@/features/map/constants/layerMetadata';
import { fetchLayer, zoomLevelFor } from '@/features/map/services/layersApi';
import type { ZoomLevel } from '@/features/map/services/layersApi';
import { fetchShapefileFeatures } from '@/features/data/services/shapefilesApi';
import {
  getStoredVisibleIds,
  storeVisibleIds,
  getStoredVisibleUploadIds,
  storeVisibleUploadIds,
} from '@/features/map/utils/layerVisibility';

const MAP_CONTAINER_ID = 'geoavia-map';

export function MapComponent() {
  const { user } = useAuth();
  const isDevUser = user?.role === 'administrador';

  const [activeBaseMap, setActiveBaseMap] = useState<'satellite' | 'osm'>('osm');
  const [isLayerPanelOpen, setIsLayerPanelOpen] = useState(false);
  const [isRegionPanelOpen, setIsRegionPanelOpen] = useState(false);
  const [selectedLayerMeta, setSelectedLayerMeta] = useState<LayerMetadata | null>(null);
  const [showDebug, setShowDebug] = useState(false);

  // Layers and Region panels share the top-left corner, so opening one closes the other.
  const toggleLayerPanel = useCallback(() => {
    setIsLayerPanelOpen((prev) => {
      if (!prev) setIsRegionPanelOpen(false);
      return !prev;
    });
  }, []);

  const toggleRegionPanel = useCallback(() => {
    setIsRegionPanelOpen((prev) => {
      if (!prev) setIsLayerPanelOpen(false);
      return !prev;
    });
  }, []);

  // Static LAYER_REGISTRY layers — initialized from localStorage so LayerConfigPage changes persist
  const [visibleLayers, setVisibleLayers] = useState<Set<string>>(getStoredVisibleIds);

  // User-uploaded shapefile layers — initialized from localStorage so the
  // selection survives a refresh (mirrors the static layers above).
  const [visibleUploads, setVisibleUploads] = useState<Set<number>>(getStoredVisibleUploadIds);

  const [currentZoomLevel, setCurrentZoomLevel] = useState<ZoomLevel>('z1');

  // Bumped (debounced) on map pan/zoom so viewport-filtered uploads refetch.
  const [bboxTick, setBboxTick] = useState(0);

  // Tracks the resolution token currently sourced for each layer/upload key.
  // Static layers store a ZoomLevel; uploads store a zoom or "z3:<bbox>" token.
  const sourceVersions = useRef<Map<string, string>>(new Map());

  const toggleLayer = useCallback((id: string) => {
    setVisibleLayers((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      storeVisibleIds(next);
      return next;
    });
  }, []);

  const toggleUpload = useCallback((id: number) => {
    setVisibleUploads((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      storeVisibleUploadIds(next);
      return next;
    });
  }, []);

  const mapStyle = import.meta.env.VITE_MAPLIBRE_STYLE_URL;

  const { map, isMapReady, setBaseMap, flyTo, cursorPosition } = useMap({
    containerId: MAP_CONTAINER_ID,
    styleUrl: mapStyle,
  });

  const handleBaseMapChange = useCallback(
    (layer: 'satellite' | 'osm') => {
      setActiveBaseMap(layer);
      setBaseMap(layer);
    },
    [setBaseMap]
  );

  const handleRegionSelect = useCallback(
    (center: [number, number], zoom: number) => flyTo(center, zoom),
    [flyTo]
  );

  // Click handler for secure popups on static vector layers
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

  // Track zoom bucket
  useEffect(() => {
    const m = map.current;
    if (!m || !isMapReady) return;

    const handleZoom = () => {
      const next = zoomLevelFor(m.getZoom());
      setCurrentZoomLevel((prev) => (prev === next ? prev : next));
    };

    handleZoom();
    m.on('zoomend', handleZoom);
    return () => { m.off('zoomend', handleZoom); };
  }, [map, isMapReady]);

  // Debounced pan/zoom signal so viewport-filtered uploads refetch on move
  useEffect(() => {
    const m = map.current;
    if (!m || !isMapReady) return;

    let timer: ReturnType<typeof setTimeout> | undefined;
    const handleMove = () => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => setBboxTick((v) => v + 1), 300);
    };

    m.on('moveend', handleMove);
    return () => { if (timer) clearTimeout(timer); m.off('moveend', handleMove); };
  }, [map, isMapReady]);

  // Sync static LAYER_REGISTRY layers
  useEffect(() => {
    const m = map.current;
    if (!m || !isMapReady) return;

    const SOURCE_PREFIX = 'data-layer-';
    const LAYER_PREFIX = 'data-layer-';
    const tracked = sourceVersions.current;

    const sync = async () => {
      // Remove layers no longer visible
      for (const id of Array.from(tracked.keys())) {
        if (id.startsWith('upload-')) continue; // handled separately
        if (visibleLayers.has(id)) continue;
        const layerId = `${LAYER_PREFIX}${id}`;
        const sourceId = `${SOURCE_PREFIX}${id}`;
        if (m.getLayer(layerId)) m.removeLayer(layerId);
        if (m.getSource(sourceId)) m.removeSource(sourceId);
        tracked.delete(id);
      }

      // Add or refetch visible static layers
      for (const id of visibleLayers) {
        const meta = LAYER_REGISTRY.find((l) => l.id === id);
        if (!meta || meta.available === false || !meta.backendName || !meta.paint) continue;
        if (tracked.get(id) === currentZoomLevel) continue;

        const geojson = await fetchLayer({
          layerName: meta.backendName,
          zoom: currentZoomLevel,
        });

        const sourceId = `${SOURCE_PREFIX}${id}`;
        const layerId = `${LAYER_PREFIX}${id}`;

        const existing = m.getSource(sourceId);
        if (existing) {
          (existing as maplibregl.GeoJSONSource).setData(geojson);
        } else {
          m.addSource(sourceId, { type: 'geojson', data: geojson });
          m.addLayer({
            id: layerId,
            type: meta.paint.maplibreType,
            source: sourceId,
            paint: meta.paint.paint,
          } as maplibregl.AddLayerObject);
        }
        tracked.set(id, currentZoomLevel);
      }
    };

    sync().catch((err) => {
      console.error('[MapComponent] Failed to sync data layers', err);
    });
  }, [map, isMapReady, visibleLayers, currentZoomLevel]);

  // Sync user-uploaded layers
  useEffect(() => {
    const m = map.current;
    if (!m || !isMapReady) return;

    const tracked = sourceVersions.current;
    // Cancels in-flight feature fetches when this effect re-runs (toggle off,
    // zoom/pan). Without it, a slow response could arrive after a layer was
    // turned off and wrongly re-add it (stale-response race).
    const controller = new AbortController();

    const syncUploads = async () => {
      // Remove de-selected upload layers
      for (const key of Array.from(tracked.keys())) {
        if (!key.startsWith('upload-')) continue;
        const uploadId = Number(key.replace('upload-', ''));
        if (visibleUploads.has(uploadId)) continue;
        if (m.getLayer(key)) m.removeLayer(key);
        if (m.getSource(key)) m.removeSource(key);
        tracked.delete(key);
      }

      // Bbox filtering only at the most detailed zoom; z1/z2 load the whole
      // (simplified) base since it's already light enough to render.
      const useBbox = currentZoomLevel === 'z3';
      const b = useBbox ? m.getBounds() : null;
      const bbox: [number, number, number, number] | undefined = b
        ? [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()]
        : undefined;
      // Round the bbox so tiny pans don't trigger a refetch.
      const token = bbox
        ? `z3:${bbox.map((n) => n.toFixed(2)).join(',')}`
        : currentZoomLevel;

      // Add or refetch visible upload layers
      for (const uploadId of visibleUploads) {
        const key = `upload-${uploadId}`;
        if (tracked.get(key) === token) continue; // already at this resolution/viewport

        try {
          const geojson = await fetchShapefileFeatures({
            uploadId,
            zoom: currentZoomLevel,
            bbox,
            signal: controller.signal,
          });

          // A newer run superseded this one (toggle/zoom/pan): drop the stale
          // response so it can't re-add a layer the user already turned off.
          if (controller.signal.aborted) return;

          const existing = m.getSource(key);
          if (existing) {
            (existing as maplibregl.GeoJSONSource).setData(geojson);
          } else {
            m.addSource(key, { type: 'geojson', data: geojson });
            m.addLayer({
              id: key,
              type: 'line',
              source: key,
              paint: { 'line-color': '#f97316', 'line-width': 2, 'line-opacity': 0.85 },
            });
          }
          tracked.set(key, token);
        } catch (err) {
          if (controller.signal.aborted) return; // expected on supersede
          console.error(`[MapComponent] Failed to load upload ${uploadId}`, err);
        }
      }
    };

    syncUploads().catch((err) => {
      if (controller.signal.aborted) return;
      console.error('[MapComponent] Upload sync error', err);
    });

    return () => controller.abort();
  }, [map, isMapReady, visibleUploads, currentZoomLevel, bboxTick]);

  return (
    <div className="relative h-full w-full">
      <div id={MAP_CONTAINER_ID} className="h-full w-full" />

      {/* Toolbar — top-left buttons */}
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <button
          onClick={toggleLayerPanel}
          className={`rounded-lg shadow-md border border-neutral-200/50 p-2.5 transition-all ${
            isLayerPanelOpen ? 'bg-accent-500 text-white' : 'bg-white/90 backdrop-blur-md text-neutral-600 hover:text-primary-600 hover:bg-white'
          }`}
          aria-label="Painel de camadas"
          aria-pressed={isLayerPanelOpen}
          type="button"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.429 9.75L2.25 12l4.179 2.25m0-4.5l5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0l4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0l-5.571 3-5.571-3" />
          </svg>
        </button>
        <button
          onClick={toggleRegionPanel}
          className={`rounded-lg shadow-md border border-neutral-200/50 p-2.5 transition-all ${
            isRegionPanelOpen ? 'bg-accent-500 text-white' : 'bg-white/90 backdrop-blur-md text-neutral-600 hover:text-primary-600 hover:bg-white'
          }`}
          aria-label="Painel de região e estado"
          aria-pressed={isRegionPanelOpen}
          type="button"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
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
            visibleLayers={visibleLayers}
            onToggleLayer={toggleLayer}
            visibleUploads={visibleUploads}
            onToggleUpload={toggleUpload}
          />
        </div>
      )}

      {/* Region Selector — toggleable panel (top-left, mirrors the layers panel) */}
      {isRegionPanelOpen && (
        <div className="absolute top-16 left-4 z-20">
          <RegionSelector
            onRegionSelect={handleRegionSelect}
            onClose={() => setIsRegionPanelOpen(false)}
          />
        </div>
      )}

      {/* Base Map Control */}
      <LayerControl activeLayer={activeBaseMap} onLayerChange={handleBaseMapChange} />

      {/* CRS Label */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-10 rounded-md bg-white/90 backdrop-blur-md shadow-sm border border-neutral-200/50 px-2 py-1 text-[10px] font-mono text-neutral-600">
        {CRS_LABEL}
      </div>

      {/* Debug overlay (dev only) */}
      {showDebug && isDevUser && cursorPosition && (
        <div className="absolute top-4 right-16 z-10 rounded-lg bg-white/90 backdrop-blur-md shadow-md border border-neutral-200/50 px-3 py-2 text-xs font-mono space-y-0.5">
          <div><span className="text-neutral-500">Lng:</span> <span className="text-accent-600">{cursorPosition.lng.toFixed(6)}</span></div>
          <div><span className="text-neutral-500">Lat:</span> <span className="text-accent-600">{cursorPosition.lat.toFixed(6)}</span></div>
        </div>
      )}

      {/* Assessment rectangles (sítios avaliados) */}
      <AssessmentMarkers map={map} isMapReady={isMapReady} />

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
