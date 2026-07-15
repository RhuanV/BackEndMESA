/**
 * MetadataModal — Displays layer metadata (RF01 metadata viewer).
 *
 * When the layer has a `catalogKey`, live metadata is fetched from the backend
 * catalog API (mesa_a.layer_catalog) — the single source of truth populated
 * from the metadata spreadsheet. Otherwise it falls back to the static registry
 * fields. The catalog is also used as a graceful fallback if the request fails.
 *
 * Security: All values are sanitized via DOMPurify before rendering
 * (Defense in Depth).
 */
import { Modal } from '@/components/ui';
import { sanitize } from '@/lib/security/sanitize';
import type { LayerMetadata } from '@/features/map/constants/layerMetadata';
import { useCatalogLayer } from '@/features/map/hooks/useCatalogLayer';

interface MetadataModalProps {
  readonly layer: LayerMetadata | null;
  readonly onClose: () => void;
}

interface Field {
  readonly label: string;
  readonly value: string | null | undefined;
}

const typeLabel = (type: LayerMetadata['type']): string =>
  type === 'raster' ? 'Matricial (Raster)' : 'Vetorial (Vector)';

export function MetadataModal({ layer, onClose }: MetadataModalProps) {
  // Hook must run unconditionally; it stays idle when there is no catalogKey.
  const { data: catalog, isLoading } = useCatalogLayer(layer?.catalogKey ?? null);

  if (!layer) return null;

  // Prefer catalog metadata; fall back to the static registry fields.
  const fields: Field[] = catalog
    ? [
        { label: 'Tema', value: catalog.tema },
        { label: 'Plano de Informação', value: catalog.plano_informacao },
        { label: 'Fonte', value: catalog.fonte },
        { label: 'Última Atualização', value: catalog.data_atualizacao_fonte },
        { label: 'Periodicidade', value: catalog.periodicidade },
        { label: 'Sistema de Referência', value: catalog.datum },
        { label: 'EPSG', value: catalog.epsg },
        { label: 'Formato', value: catalog.formato },
        { label: 'Geometria', value: catalog.geometria },
        { label: 'Segregação', value: catalog.segregacao },
        { label: 'Observações', value: catalog.observacoes },
        { label: 'Endereço', value: catalog.endereco },
      ]
    : [
        { label: 'Fonte', value: layer.source },
        { label: 'Última Atualização', value: layer.lastUpdate },
        { label: 'Sistema de Referência', value: layer.epsg },
        { label: 'Tipo', value: typeLabel(layer.type) },
        { label: 'Descrição', value: layer.description },
      ];

  const visibleFields = fields.filter((f) => f.value != null && f.value !== '');

  return (
    <Modal isOpen={true} onClose={onClose} title={sanitize(layer.name)} maxWidth="md">
      {isLoading && !catalog ? (
        <p className="text-sm text-neutral-500">Carregando metadados do catálogo…</p>
      ) : (
        <div className="space-y-3">
          {visibleFields.map((field) => (
            <div key={field.label} className="flex flex-col gap-1 rounded-lg bg-neutral-50 p-3">
              <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
                {field.label}
              </span>
              <span className="text-sm text-neutral-800 whitespace-pre-line">
                {sanitize(field.value ?? '')}
              </span>
            </div>
          ))}
        </div>
      )}
    </Modal>
  );
}
