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
import {
  BRAZIL_BOUNDS,
  BRAZIL_CENTER,
  DEFAULT_ZOOM,
  MIN_ZOOM,
  MAX_ZOOM,
} from '@/features/map/constants/bounds';

interface UseMapOptions {
  readonly containerId: string;
  readonly styleUrl?: string;
}

export function useMap({ containerId, styleUrl }: UseMapOptions) {
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [isMapReady, setIsMapReady] = useState(false);
  const [cursorPosition, setCursorPosition] = useState<{ lng: number; lat: number } | null>(null);

  useEffect(() => {
    const container = document.getElementById(containerId);
    if (!container || mapRef.current) return;

    const resolvedStyle =
      styleUrl ?? import.meta.env.VITE_MAPLIBRE_STYLE_URL ?? 'https://demotiles.maplibre.org/style.json';

    if (import.meta.env.PROD && !resolvedStyle.startsWith('https://')) {
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

    map.on('load', () => setIsMapReady(true));

    // Track cursor for debug display
    map.on('mousemove', (e) => {
      setCursorPosition({ lng: e.lngLat.lng, lat: e.lngLat.lat });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      setIsMapReady(false);
    };
  }, [containerId, styleUrl]);

  const setStyle = useCallback((newStyleUrl: string) => {
    if (mapRef.current) {
      mapRef.current.setStyle(newStyleUrl);
    }
  }, []);

  const flyTo = useCallback((center: [number, number], zoom: number) => {
    if (mapRef.current) {
      mapRef.current.flyTo({ center, zoom, duration: 1500 });
    }
  }, []);

  return { map: mapRef, isMapReady, setStyle, flyTo, cursorPosition };
}
