/**
 * ExportPage — Download analysis results as Shapefile or GeoTIFF.
 *
 * Security: Downloads via proxied Axios (never direct external URLs).
 */
import { useState } from 'react';
import { Button, Input, ProgressBar } from '@/components/ui';
import { downloadExport } from '@/features/analysis/services/analysisService';

export function ExportPage() {
  const [isExporting, setIsExporting] = useState(false);
  const [exportType, setExportType] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [codigoIbge, setCodigoIbge] = useState('');

  const handleExport = async (format: 'shapefile' | 'geotiff') => {
    setIsExporting(true);
    setExportType(format);
    setError(null);
    try {
      const blob = await downloadExport(
        format,
        format === 'geotiff' ? { codigoIbge: codigoIbge.trim() } : undefined,
      );
      const filename =
        format === 'shapefile' ? 'mesa_ranking.zip' : `mesa_suitability_${codigoIbge.trim()}.tif`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      // Surface backend detail when present (e.g., 501 for GeoTIFF, 400 if no
      // assessments) instead of a generic message.
      let detail: string | undefined;
      if (err && typeof err === 'object' && 'response' in err) {
        const data = (err as { response?: { data?: { detail?: string } | Blob } }).response?.data;
        if (data instanceof Blob) {
          try {
            detail = JSON.parse(await data.text()).detail;
          } catch {
            /* keep undefined */
          }
        } else if (data && typeof data === 'object') {
          detail = data.detail;
        }
      }
      setError(detail ?? 'Erro ao exportar. Verifique se há resultados disponíveis.');
    } finally {
      setIsExporting(false);
      setExportType(null);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">Exportar Resultados</h2>
        <p className="mt-1 text-sm text-neutral-500">
          Baixe os resultados da análise MESA nos formatos Shapefile ou GeoTIFF.
        </p>
      </div>

      {error && (
        <div role="alert" className="mb-4 rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600">{error}</div>
      )}

      {isExporting && (
        <div className="mb-4">
          <ProgressBar label={`Exportando ${exportType}...`} />
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-neutral-200 bg-surface p-6 shadow-sm text-center">
          <div className="text-4xl mb-3" aria-hidden="true">📐</div>
          <h3 className="text-sm font-semibold text-neutral-900 mb-1">Shapefile (.shp)</h3>
          <p className="text-xs text-neutral-500 mb-4">Formato vetorial compatível com QGIS e ArcGIS.</p>
          <Button onClick={() => void handleExport('shapefile')} disabled={isExporting} className="w-full">
            Baixar Shapefile
          </Button>
        </div>
        <div className="rounded-xl border border-neutral-200 bg-surface p-6 shadow-sm text-center">
          <div className="text-4xl mb-3" aria-hidden="true">🗺️</div>
          <h3 className="text-sm font-semibold text-neutral-900 mb-1">GeoTIFF (.tif)</h3>
          <p className="text-xs text-neutral-500 mb-3">
            Mapa de adequabilidade (MCDA) do município em SIRGAS 2000 (RF03/RF05).
          </p>
          <div className="mb-3 text-left">
            <Input
              label="Código IBGE do município"
              value={codigoIbge}
              onChange={(e) => setCodigoIbge(e.target.value)}
              maxLength={7}
              placeholder="ex.: 3550308"
            />
          </div>
          <Button
            onClick={() => void handleExport('geotiff')}
            disabled={isExporting || codigoIbge.trim().length === 0}
            className="w-full"
          >
            Baixar GeoTIFF
          </Button>
        </div>
      </div>
    </div>
  );
}
