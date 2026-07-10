/**
 * useMap — MapLibre GL JS lifecycle with Brazil bounds and debug support.
 *
 * Enhanced for Sprint 2:
 * - maxBounds for Brazilian territory
 * - flyTo for region selection
 * - Debug mode (coordinates + FPS)
 * - Proper cleanup on unmount
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import type { StyleSpecification } from 'maplibre-gl';
import {
  BRAZIL_BOUNDS,
  BRAZIL_CENTER,
  DEFAULT_ZOOM,
  MIN_ZOOM,
  MAX_ZOOM,
} from '@/features/map/constants/bounds';

/**
 * Inline OSM raster style — used when no VITE_MAPLIBRE_STYLE_URL is set, or
 * when the env points to MapLibre's empty global demo style. Renders the
 * actual basemap of Brazil via OSM tiles, no API key required.
 */
const OSM_RASTER_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
      maxzoom: 19,
    },
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
};

/**
 * Google Satellite Hybrid raster style — renders high-resolution satellite imagery
 * with roads and labels overlay.
 */
const GOOGLE_HYBRID_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    'google-hybrid': {
      type: 'raster',
      tiles: ['https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'],
      tileSize: 256,
      attribution: '© Google',
      maxzoom: 20,
    },
  },
  layers: [{ id: 'google-hybrid', type: 'raster', source: 'google-hybrid' }],
};

const isUnusableStyle = (url: string | undefined) =>
  !url || url.includes('demotiles.maplibre.org');

const resolveStyle = (style: string | StyleSpecification | undefined): string | StyleSpecification => {
  if (style === 'google-hybrid') {
    return GOOGLE_HYBRID_STYLE;
  }
  if (style === 'osm') {
    return OSM_RASTER_STYLE;
  }
  if (!style || (typeof style === 'string' && isUnusableStyle(style))) {
    return OSM_RASTER_STYLE;
  }
  return style as string | StyleSpecification;
};

interface UseMapOptions {
  readonly containerId: string;
  readonly styleUrl?: string | StyleSpecification;
}

export function useMap({ containerId, styleUrl }: UseMapOptions) {
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [isMapReady, setIsMapReady] = useState(false);
  const [cursorPosition, setCursorPosition] = useState<{ lng: number; lat: number } | null>(null);

  useEffect(() => {
    const container = document.getElementById(containerId);
    if (!container || mapRef.current) return;

    const envStyle = styleUrl ?? import.meta.env.VITE_MAPLIBRE_STYLE_URL;
    const resolvedStyle = resolveStyle(envStyle);

    if (
      import.meta.env.PROD &&
      typeof resolvedStyle === 'string' &&
      !resolvedStyle.startsWith('https://')
    ) {
      console.warn('[Security] MapLibre style URL should use HTTPS in production:', resolvedStyle);
    }

    const map = new maplibregl.Map({
      container,
      style: resolvedStyle,
      center: BRAZIL_CENTER,
      zoom: DEFAULT_ZOOM,
      minZoom: MIN_ZOOM,
      maxZoom: MAX_ZOOM,
      maxBounds: BRAZIL_BOUNDS,
      attributionControl: {},
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.ScaleControl(), 'bottom-left');

    const timer = setTimeout(() => {
      console.warn('[Map] Safety load timeout triggered - forcing isMapReady=true');
      setIsMapReady(true);
    }, 1500);

    const onLoad = () => {
      clearTimeout(timer);
      const m = mapRef.current;
      if (!m) return;

      try {
        // 1) Add OSM source and layer if not present
        if (!m.getSource('osm')) {
          m.addSource('osm', {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors',
            maxzoom: 19,
          });
        }
        if (!m.getLayer('osm')) {
          m.addLayer({
            id: 'osm',
            type: 'raster',
            source: 'osm',
            layout: {
              visibility: envStyle ? 'none' : 'visible',
            },
          });
        }

        // 2) Add Google Hybrid source and layer if not present
        if (!m.getSource('google-hybrid')) {
          m.addSource('google-hybrid', {
            type: 'raster',
            tiles: ['https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'],
            tileSize: 256,
            attribution: '© Google',
            maxzoom: 20,
          });
        }
        if (!m.getLayer('google-hybrid')) {
          m.addLayer({
            id: 'google-hybrid',
            type: 'raster',
            source: 'google-hybrid',
            layout: {
              visibility: 'none',
            },
          });
        }
      } catch (err) {
        console.error('[Map] Error in onLoad style/layers injection:', err);
      } finally {
        setIsMapReady(true);
      }
    };

    if (map.isStyleLoaded()) {
      onLoad();
    } else {
      map.on('load', onLoad);
      // Fallback event for style loading
      map.on('style.load', onLoad);
    }

    // Track cursor for debug display
    map.on('mousemove', (e) => {
      setCursorPosition({ lng: e.lngLat.lng, lat: e.lngLat.lat });
    });

    mapRef.current = map;

    return () => {
      clearTimeout(timer);
      map.remove();
      mapRef.current = null;
      setIsMapReady(false);
    };
  }, [containerId, styleUrl]);

  const setBaseMap = useCallback((baseMapId: 'satellite' | 'osm') => {
    const m = mapRef.current;
    if (!m) return;

    const showSatellite = baseMapId === 'satellite';
    if (m.getLayer('osm')) m.setLayoutProperty('osm', 'visibility', showSatellite ? 'none' : 'visible');
    if (m.getLayer('google-hybrid')) m.setLayoutProperty('google-hybrid', 'visibility', showSatellite ? 'visible' : 'none');
  }, []);

  const flyTo = useCallback((center: [number, number], zoom: number) => {
    if (mapRef.current) {
      mapRef.current.flyTo({ center, zoom, duration: 1500 });
    }
  }, []);

  return { map: mapRef, isMapReady, setBaseMap, flyTo, cursorPosition };
}
