/**
 * LayerControl — Base map switcher (BDG MESA / Satellite / OSM).
 */

interface LayerControlProps {
  readonly activeLayer: 'bdg-mesa' | 'satellite' | 'osm';
  readonly onLayerChange: (layer: 'bdg-mesa' | 'satellite' | 'osm') => void;
}

const layers = [
  { id: 'bdg-mesa' as const, label: 'BDG MESA', icon: '🗺️' },
  { id: 'satellite' as const, label: 'Satélite', icon: '🛰️' },
  { id: 'osm' as const, label: 'OSM', icon: '🌐' },
];

export function LayerControl({ activeLayer, onLayerChange }: LayerControlProps) {
  return (
    <div
      className="absolute bottom-8 right-4 z-10 rounded-xl bg-white/90 backdrop-blur-md shadow-lg border border-neutral-200/50 p-1.5"
      role="radiogroup"
      aria-label="Mapa base"
    >
      {layers.map((layer) => (
        <button
          key={layer.id}
          onClick={() => onLayerChange(layer.id)}
          role="radio"
          aria-checked={activeLayer === layer.id}
          className={`
            flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium
            transition-all duration-200 w-full
            ${
              activeLayer === layer.id
                ? 'bg-primary-600 text-white shadow-sm'
                : 'text-neutral-600 hover:bg-neutral-100'
            }
          `}
          type="button"
        >
          <span aria-hidden="true">{layer.icon}</span>
          {layer.label}
        </button>
      ))}
    </div>
  );
}
