/**
 * LayerPanel — Tree-structured layer list with toggles and legend.
 *
 * Groups layers by: Dados Base, Análise MESA, Áreas Excludentes.
 * Each layer can be toggled visible/hidden with an info button for metadata.
 */
import { useState } from 'react';
import { LAYER_REGISTRY, getLayersByGroup } from '@/features/map/constants/layerMetadata';
import type { LayerMetadata } from '@/features/map/constants/layerMetadata';

interface LayerPanelProps {
  readonly isOpen: boolean;
  readonly onClose: () => void;
  readonly onLayerInfo: (layer: LayerMetadata) => void;
}

interface LayerGroupConfig {
  readonly key: LayerMetadata['group'];
  readonly label: string;
  readonly icon: string;
  readonly color: string;
}

const groups: readonly LayerGroupConfig[] = [
  { key: 'base', label: 'Dados Base', icon: '🗺️', color: 'text-blue-600' },
  { key: 'analysis', label: 'Análise MESA', icon: '📊', color: 'text-teal-600' },
  { key: 'exclusion', label: 'Áreas Excludentes', icon: '🚫', color: 'text-red-600' },
];

export function LayerPanel({ isOpen, onClose, onLayerInfo }: LayerPanelProps) {
  const [visibleLayers, setVisibleLayers] = useState<Set<string>>(() => {
    const defaults = new Set<string>();
    LAYER_REGISTRY.forEach((l) => { if (l.defaultVisible) defaults.add(l.id); });
    return defaults;
  });
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['base']));

  const toggleLayer = (id: string) => {
    setVisibleLayers((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleGroup = (key: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  if (!isOpen) return null;

  return (
    <div className="absolute top-4 left-4 z-20 w-72 max-h-[calc(100vh-8rem)] overflow-y-auto rounded-xl bg-white/95 backdrop-blur-md shadow-xl border border-neutral-200/50 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-neutral-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-neutral-800">Camadas</h3>
        <button onClick={onClose} className="rounded-lg p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-600 transition-colors" aria-label="Fechar painel de camadas" type="button">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Layer groups */}
      <div className="p-2 space-y-1">
        {groups.map((group) => {
          const layers = getLayersByGroup(group.key);
          const isExpanded = expandedGroups.has(group.key);

          return (
            <div key={group.key}>
              <button
                onClick={() => toggleGroup(group.key)}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold text-neutral-700 hover:bg-neutral-100 transition-colors"
                type="button"
                aria-expanded={isExpanded}
              >
                <svg className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-90' : ''}`} fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                  <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                </svg>
                <span aria-hidden="true">{group.icon}</span>
                {group.label}
                <span className="ml-auto text-[10px] text-neutral-400">{layers.length}</span>
              </button>

              {isExpanded && (
                <div className="ml-4 space-y-0.5 animate-fade-in">
                  {layers.map((layer) => (
                    <div key={layer.id} className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-neutral-50 group">
                      <input
                        type="checkbox"
                        checked={visibleLayers.has(layer.id)}
                        onChange={() => toggleLayer(layer.id)}
                        className="h-3.5 w-3.5 rounded border-neutral-300 text-primary-600 focus:ring-accent-500 cursor-pointer"
                        id={`layer-${layer.id}`}
                        aria-label={`Camada: ${layer.name}`}
                      />
                      <label htmlFor={`layer-${layer.id}`} className="flex-1 text-xs text-neutral-700 cursor-pointer select-none">
                        {layer.name}
                      </label>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${layer.type === 'raster' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
                        {layer.type === 'raster' ? 'R' : 'V'}
                      </span>
                      <button
                        onClick={() => onLayerInfo(layer)}
                        className="opacity-0 group-hover:opacity-100 rounded p-0.5 text-neutral-400 hover:text-primary-600 transition-all"
                        type="button"
                        aria-label={`Informações da camada ${layer.name}`}
                      >
                        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
