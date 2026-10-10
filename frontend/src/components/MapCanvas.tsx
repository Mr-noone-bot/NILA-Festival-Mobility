import { useEffect, useRef, useState } from 'react';
import maplibregl, { type Map as MapLibreMap, type Marker } from 'maplibre-gl';
import type { CrowdPoint, Stop } from '../types/nila';
import { Bus, MapPin, RotateCcw } from 'lucide-react';

interface MapCanvasProps {
  center: [number, number];
  stops: Stop[];
  points: CrowdPoint[];
  route?: { from: string; to: string } | null;
  routeGeometry?: [number, number][] | null;
  showHeatmap: boolean;
  onStopSelect?: (stop: Stop) => void;
}

const STYLE_URL = import.meta.env.VITE_MAP_STYLE_URL || 'https://tiles.openfreemap.org/styles/liberty';

export default function MapCanvas({
  center,
  stops,
  points,
  route,
  routeGeometry,
  showHeatmap,
  onStopSelect,
}: MapCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markersRef = useRef<Marker[]>([]);
  const [mapReady, setMapReady] = useState(false);
  const [mapError, setMapError] = useState(false);

  // Initialize Map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    let alive = true;

    try {
      const map = new maplibregl.Map({
        container: containerRef.current,
        style: STYLE_URL,
        center,
        zoom: 12.8,
        pitch: 0,
        attributionControl: false,
      });

      mapRef.current = map;
      map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), 'top-right');
      map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-left');

      map.on('load', () => {
        if (alive) {
          setMapReady(true);
          setMapError(false);
        }
      });

      map.on('error', () => {
        if (alive && !map.isStyleLoaded()) {
          setMapError(true);
        }
      });

      const resizeObserver = new ResizeObserver(() => {
        map.resize();
      });
      resizeObserver.observe(containerRef.current);

      return () => {
        alive = false;
        resizeObserver.disconnect();
        markersRef.current.forEach((marker) => marker.remove());
        markersRef.current = [];
        map.remove();
        mapRef.current = null;
      };
    } catch {
      setMapError(true);
    }
  }, [center]);

  // Center update
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;
    map.easeTo({ center, duration: 700 });
  }, [center, mapReady]);

  // Heatmap Source & Layer using native MapLibre Heatmap (GPU accelerated)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    const heatFeatures = points.map((p) => ({
      type: 'Feature' as const,
      properties: { weight: p.weight },
      geometry: { type: 'Point' as const, coordinates: p.coordinates },
    }));

    const heatData = {
      type: 'FeatureCollection' as const,
      features: showHeatmap ? heatFeatures : [],
    };

    if (map.getSource('nila-heat')) {
      (map.getSource('nila-heat') as maplibregl.GeoJSONSource).setData(heatData);
    } else {
      map.addSource('nila-heat', {
        type: 'geojson',
        data: heatData,
      });

      map.addLayer({
        id: 'nila-heat-layer',
        type: 'heatmap',
        source: 'nila-heat',
        maxzoom: 16,
        paint: {
          'heatmap-weight': ['get', 'weight'],
          'heatmap-intensity': 1.2,
          'heatmap-color': [
            'interpolate',
            ['linear'],
            ['heatmap-density'],
            0,
            'rgba(2, 132, 199, 0)',
            0.2,
            'rgba(56, 189, 248, 0.4)',
            0.5,
            'rgba(245, 158, 11, 0.7)',
            0.8,
            'rgba(239, 68, 68, 0.85)',
            1.0,
            'rgba(185, 28, 28, 0.95)',
          ],
          'heatmap-radius': 36,
          'heatmap-opacity': 0.85,
        },
      });
    }

    if (map.getLayer('nila-heat-layer')) {
      map.setLayoutProperty('nila-heat-layer', 'visibility', showHeatmap ? 'visible' : 'none');
    }
  }, [points, showHeatmap, mapReady]);

  // Markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = stops.map((stop) => {
      const element = document.createElement('button');
      element.className = `stop-marker ${stop.risk.toLowerCase()}`;
      element.type = 'button';
      element.setAttribute('aria-label', `${stop.name}, ${stop.risk.toLowerCase()} risk`);
      element.title = `${stop.name} · ${stop.currentBuses} buses · ${stop.waitMinutes} min wait`;

      const badge = document.createElement('span');
      badge.className = 'stop-marker-badge';
      badge.textContent = `${stop.currentBuses}🚌`;
      element.appendChild(badge);

      element.addEventListener('click', () => onStopSelect?.(stop));
      return new maplibregl.Marker({ element, anchor: 'center' })
        .setLngLat(stop.coordinates)
        .addTo(map);
    });
  }, [stops, mapReady, onStopSelect]);

  // Route Layer
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    const from = route ? stops.find((stop) => stop.id === route.from) : undefined;
    const to = route ? stops.find((stop) => stop.id === route.to) : undefined;
    const coordinates =
      routeGeometry?.length
        ? routeGeometry
        : from && to
        ? [
            from.coordinates,
            [(from.coordinates[0] + to.coordinates[0]) / 2 - 0.0015, (from.coordinates[1] + to.coordinates[1]) / 2 + 0.001],
            to.coordinates,
          ]
        : [];

    const geojson = {
      type: 'Feature' as const,
      properties: {},
      geometry: { type: 'LineString' as const, coordinates },
    };

    if (map.getSource('nila-route')) {
      (map.getSource('nila-route') as maplibregl.GeoJSONSource).setData({
        type: 'FeatureCollection',
        features: coordinates.length ? [geojson] : [],
      });
    } else {
      map.addSource('nila-route', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: coordinates.length ? [geojson] : [] },
      });

      map.addLayer({
        id: 'nila-route-casing',
        type: 'line',
        source: 'nila-route',
        paint: {
          'line-color': '#0369a1',
          'line-width': 7,
          'line-opacity': 0.7,
        },
      });

      map.addLayer({
        id: 'nila-route-line',
        type: 'line',
        source: 'nila-route',
        paint: {
          'line-color': '#38bdf8',
          'line-width': 4,
          'line-dasharray': [2, 1],
          'line-opacity': 1.0,
        },
      });
    }

    if (from && to && coordinates.length > 0) {
      map.fitBounds([from.coordinates, to.coordinates], {
        padding: { top: 70, bottom: 70, left: 70, right: 70 },
        maxZoom: 13.5,
        duration: 600,
      });
    }
  }, [route, routeGeometry, stops, mapReady]);

  return (
    <div className="map-frame">
      <div
        ref={containerRef}
        className="map-canvas"
        aria-label="Interactive festival crowd and transport map"
      />

      {!mapReady && !mapError && (
        <div className="map-overlay-state">
          <span className="spinner" /> Loading festival geospatial tiles…
        </div>
      )}

      {mapError && (
        <div className="map-overlay-state map-error">
          <MapPin size={22} className="text-sky-600 mb-1" />
          <div className="text-center font-medium text-slate-800">
            Map tiles currently unavailable offline
          </div>
          <span className="text-xs text-slate-600 max-w-xs text-center">
            Stop markers and repositioning routes remain available in the interface.
          </span>
          <button
            className="mt-2 px-3 py-1 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
            onClick={() => {
              setMapError(false);
              mapRef.current?.setStyle(STYLE_URL);
            }}
          >
            <RotateCcw size={14} /> Retry Map Tiles
          </button>
        </div>
      )}

      <div className="map-floating-label">
        <span className="live-dot" /> MADURAI · FESTIVAL GEOGRAPHY{' '}
        <span className="map-label-divider">·</span>{' '}
        {showHeatmap ? 'DENSITY OVERLAY ACTIVE' : 'DENSITY OVERLAY OFF'}
      </div>

      <div className="map-legend">
        <div className="legend-title">PREDICTED CROWD DENSITY</div>
        <div className="legend-gradient" />
        <div className="legend-scale">
          <span>Low</span>
          <span>Moderate</span>
          <span>High</span>
          <span>Critical</span>
        </div>
        <div className="legend-footnote">Model aggregate · Zero-sum fleet allocation</div>
      </div>

      <div className="map-stop-count">
        <Bus size={14} className="text-sky-600" />
        <span className="font-semibold text-slate-800">{stops.length} stops</span>
        <span>·</span>
        <span className="text-sky-700 font-bold">
          {stops.reduce((sum, stop) => sum + stop.currentBuses, 0)} buses deployed
        </span>
      </div>
    </div>
  );
}
