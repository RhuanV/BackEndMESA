/**
 * ShapefileImportPage — Upload de shapefiles (Sprint 5 HU-31).
 *
 * Acesso: operador, supervisor, gestor, coordenador, administrador (gate no router).
 * Backend reprojeta automaticamente pra SIRGAS 2000 (EPSG:4674).
 */
import { useState, useEffect, useCallback } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import {
  listShapefiles,
  uploadShapefile,
  type UploadedLayer,
} from '@/features/data/services/shapefilesApi';
import { sanitize } from '@/lib/security/sanitize';

export function ShapefileImportPage() {
  const [uploads, setUploads] = useState<UploadedLayer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [layerName, setLayerName] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  const refreshList = useCallback(async () => {
    try {
      const list = await listShapefiles();
      setUploads(list);
      setError(null);
    } catch {
      setError('Erro ao carregar a lista de uploads.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
    if (selected && !layerName) {
      // Default layer name = filename without extension
      setLayerName(selected.name.replace(/\.zip$/i, ''));
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!file) {
      setFormError('Selecione um arquivo ZIP.');
      return;
    }
    setFormError(null);
    setFormSuccess(null);
    setIsSubmitting(true);
    try {
      const result = await uploadShapefile({
        file,
        layerName: layerName.trim(),
        description: description.trim() || undefined,
      });
      setFormSuccess(
        `Camada "${result.layer_name}" importada com ${result.feature_count} feature(s) ` +
          `(SRID origem: ${result.source_srid ?? 'desconhecido'}, alvo: ${result.target_srid}).`
      );
      setFile(null);
      setLayerName('');
      setDescription('');
      (document.getElementById('shapefile-input') as HTMLInputElement | null)?.value &&
        ((document.getElementById('shapefile-input') as HTMLInputElement).value = '');
      await refreshList();
    } catch (err) {
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setFormError(detail ?? 'Falha ao importar o shapefile.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">Importar Shapefile</h2>
        <p className="mt-1 text-sm text-neutral-500">
          Envie um arquivo ZIP contendo .shp + .dbf + .shx (+ .prj recomendado). Limite: 500 MB.
          Geometrias são reprojetadas automaticamente para SIRGAS 2000 (EPSG:4674).
        </p>
      </div>

      <div className="mb-8 rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-neutral-900">Novo upload</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="shapefile-input"
              className="block text-sm font-medium text-neutral-700 mb-1.5"
            >
              Arquivo ZIP
            </label>
            <input
              id="shapefile-input"
              type="file"
              accept=".zip,application/zip"
              onChange={handleFileChange}
              required
              className="block w-full text-sm text-neutral-600 file:mr-4 file:rounded-lg file:border-0 file:bg-primary-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-primary-700 hover:file:bg-primary-100"
            />
          </div>

          <Input
            label="Nome da camada"
            type="text"
            value={layerName}
            onChange={(e) => setLayerName(e.target.value)}
            required
            minLength={1}
            maxLength={150}
            helperText="Como essa camada aparecerá no histórico."
          />

          <Input
            label="Descrição (opcional)"
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={1000}
          />

          <div className="flex items-center justify-between gap-4">
            <div className="text-sm" aria-live="polite">
              {formError && <p role="alert" className="text-danger-600">{formError}</p>}
              {formSuccess && <p className="text-emerald-600">{formSuccess}</p>}
            </div>
            <Button type="submit" size="sm" disabled={isSubmitting || !file}>
              {isSubmitting ? 'Importando...' : 'Importar'}
            </Button>
          </div>
        </form>
      </div>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600"
        >
          {error}
        </div>
      )}

      <div className="rounded-xl border border-neutral-200 bg-white shadow-sm overflow-hidden">
        <div className="border-b border-neutral-200 bg-neutral-50 px-4 py-3">
          <h3 className="text-sm font-semibold text-neutral-700">Uploads anteriores</h3>
        </div>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
          </div>
        ) : (
          <table className="w-full text-sm" aria-label="Lista de shapefiles importados">
            <thead>
              <tr className="border-b border-neutral-200 bg-neutral-50/50">
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Camada</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Usuário</th>
                <th scope="col" className="px-4 py-3 text-right font-semibold text-neutral-700">Features</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">SRID origem</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Data</th>
              </tr>
            </thead>
            <tbody>
              {uploads.map((u) => (
                <tr
                  key={u.id}
                  className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-neutral-900">{sanitize(u.layer_name)}</div>
                    {u.description && (
                      <div className="text-xs text-neutral-500">{sanitize(u.description)}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-neutral-700">
                    {sanitize(u.username)}{' '}
                    <span className="text-xs text-neutral-400">({sanitize(u.user_role)})</span>
                  </td>
                  <td className="px-4 py-3 text-right text-neutral-700">{u.feature_count}</td>
                  <td className="px-4 py-3 text-neutral-500">
                    {u.source_srid ? `EPSG:${u.source_srid}` : '—'}
                  </td>
                  <td className="px-4 py-3 text-neutral-500">
                    {new Date(u.uploaded_at).toLocaleString('pt-BR')}
                  </td>
                </tr>
              ))}
              {uploads.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-neutral-400">
                    Nenhum upload registrado ainda.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
