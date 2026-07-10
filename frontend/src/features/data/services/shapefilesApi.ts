/**
 * Shapefiles API client (Sprint 5 HU-31).
 *
 * Wraps POST /shapefiles/upload, GET /shapefiles and GET /shapefiles/{id}/features.
 */
import type { FeatureCollection } from 'geojson';
import apiClient from '@/lib/api/axiosInstance';
import type { ZoomLevel } from '@/features/map/services/layersApi';

export interface UploadedLayer {
  readonly id: number;
  readonly layer_name: string;
  readonly description: string | null;
  readonly user_id: number | null;
  readonly username: string;
  readonly user_role: string;
  readonly original_filename: string | null;
  readonly source_srid: number | null;
  readonly feature_count: number;
  readonly uploaded_at: string;
}

export interface UploadResult {
  readonly upload_id: number;
  readonly layer_name: string;
  readonly feature_count: number;
  readonly source_srid: number | null;
  readonly target_srid: number;
}

export async function uploadShapefile(params: {
  readonly file: File;
  readonly layerName: string;
  readonly description?: string;
}): Promise<UploadResult> {
  const formData = new FormData();
  formData.append('file', params.file);
  formData.append('layer_name', params.layerName);
  if (params.description) {
    formData.append('description', params.description);
  }

  const response = await apiClient.post<UploadResult>(
    '/shapefiles/upload',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 10 * 60 * 1000,  // 10 min — large shapefiles can take a while to upload + reproject
    }
  );
  return response.data;
}

export async function listShapefiles(limit = 100): Promise<UploadedLayer[]> {
  const response = await apiClient.get<{ uploads: UploadedLayer[] }>('/shapefiles', {
    params: { limit },
  });
  return response.data.uploads;
}

export async function fetchShapefileFeatures(params: {
  readonly uploadId: number;
  readonly zoom: ZoomLevel;
  readonly bbox?: readonly [number, number, number, number];
  readonly signal?: AbortSignal;
}): Promise<FeatureCollection> {
  const query: Record<string, string> = { zoom: params.zoom };
  if (params.bbox) {
    query['bbox'] = params.bbox.join(',');
  }

  const response = await apiClient.get<FeatureCollection>(
    `/shapefiles/${params.uploadId}/features`,
    { params: query, signal: params.signal }
  );
  return response.data;
}
