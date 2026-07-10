/**
 * MetadataModal — Displays layer metadata from the registry.
 *
 * Security: All values are sanitized via DOMPurify before rendering
 * (Defense in Depth — even though data comes from a local registry,
 * future versions may fetch from an API).
 */
import { Modal } from '@/components/ui';
import { sanitize } from '@/lib/security/sanitize';
import type { LayerMetadata } from '@/features/map/constants/layerMetadata';

interface MetadataModalProps {
  readonly layer: LayerMetadata | null;
  readonly onClose: () => void;
}

export function MetadataModal({ layer, onClose }: MetadataModalProps) {
  if (!layer) return null;

  const fields = [
    { label: 'Fonte', value: layer.source },
    { label: 'Última Atualização', value: layer.lastUpdate },
    { label: 'Sistema de Referência', value: layer.epsg },
    { label: 'Tipo', value: layer.type === 'raster' ? 'Matricial (Raster)' : 'Vetorial (Vector)' },
    { label: 'Descrição', value: layer.description },
  ];

  return (
    <Modal isOpen={true} onClose={onClose} title={sanitize(layer.name)} maxWidth="md">
      <div className="space-y-3">
        {fields.map((field) => (
          <div key={field.label} className="flex flex-col gap-1 rounded-lg bg-neutral-50 p-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
              {field.label}
            </span>
            <span className="text-sm text-neutral-800">
              {sanitize(field.value)}
            </span>
          </div>
        ))}
      </div>
    </Modal>
  );
}
