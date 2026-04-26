/**
 * LayerConfigPage — Admin-only global layer configuration.
 */
import { LAYER_REGISTRY } from '@/features/map/constants/layerMetadata';

export function LayerConfigPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">Configuração de Camadas</h2>
        <p className="mt-1 text-sm text-neutral-500">Gerencie camadas globais e configurações padrão.</p>
      </div>

      <div className="space-y-3">
        {LAYER_REGISTRY.map((layer) => (
          <div key={layer.id} className="flex items-center justify-between rounded-xl border border-neutral-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3">
              <span className={`inline-flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold ${
                layer.type === 'raster' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
              }`}>
                {layer.type === 'raster' ? 'R' : 'V'}
              </span>
              <div>
                <p className="text-sm font-medium text-neutral-900">{layer.name}</p>
                <p className="text-xs text-neutral-400">{layer.source}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                layer.group === 'exclusion' ? 'bg-red-100 text-red-700' : layer.group === 'analysis' ? 'bg-teal-100 text-teal-700' : 'bg-neutral-100 text-neutral-600'
              }`}>
                {layer.group}
              </span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked={layer.defaultVisible} className="sr-only peer" />
                <div className="w-9 h-5 bg-neutral-300 peer-focus:ring-2 peer-focus:ring-accent-500 rounded-full peer peer-checked:bg-primary-600 transition-colors after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-full" />
              </label>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
