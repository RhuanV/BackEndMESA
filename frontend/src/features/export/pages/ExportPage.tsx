/**
 * ExportPage — Download analysis results as Shapefile or GeoTIFF.
 *
 * Security: Downloads via proxied Axios (never direct external URLs).
 */
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { downloadExport } from '@/features/analysis/services/analysisService';

export function ExportPage() {
  const [isExporting, setIsExporting] = useState(false);
  const [exportType, setExportType] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (format: 'shapefile' | 'geotiff') => {
    setIsExporting(true);
    setExportType(format);
    setError(null);
    try {
      const blob = await downloadExport(format);
      const filename = format === 'shapefile' ? 'mesa_ranking.zip' : 'mesa_ranking.tif';
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
        <div className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm text-center">
          <div className="text-4xl mb-3" aria-hidden="true">📐</div>
          <h3 className="text-sm font-semibold text-neutral-900 mb-1">Shapefile (.shp)</h3>
          <p className="text-xs text-neutral-500 mb-4">Formato vetorial compatível com QGIS e ArcGIS.</p>
          <Button onClick={() => void handleExport('shapefile')} disabled={isExporting} className="w-full">
            Baixar Shapefile
          </Button>
        </div>
        <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-6 shadow-sm text-center opacity-75">
          <div className="text-4xl mb-3" aria-hidden="true">🗺️</div>
          <div className="mb-1 flex items-center justify-center gap-2">
            <h3 className="text-sm font-semibold text-neutral-900">GeoTIFF (.tif)</h3>
            <span className="rounded-full bg-neutral-200 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-neutral-600">
              em breve
            </span>
          </div>
          <p className="text-xs text-neutral-500 mb-4">Depende do pipeline de dados matriciais (RF03).</p>
          <Button disabled className="w-full" title="GeoTIFF ainda não disponível">
            Indisponível
          </Button>
        </div>
      </div>
    </div>
  );
}
