/**
 * Admin API client for custom permission profiles and user role/profile edits.
 *
 * All calls are authenticated via the shared axios instance and gated on the
 * backend (admin:profiles / user-management roles). The UI gating that uses
 * these is defense in depth only.
 */
import apiClient from '@/lib/api/axiosInstance';

export interface PermissionProfile {
  readonly id: number;
  readonly name: string;
  readonly description: string | null;
  readonly permissions: readonly string[];
  readonly is_system: boolean;
}

export async function listProfiles(): Promise<PermissionProfile[]> {
  const res = await apiClient.get<{ profiles: PermissionProfile[] }>('/profiles');
  return res.data.profiles;
}

export async function listPermissionCatalog(): Promise<string[]> {
  const res = await apiClient.get<{ permissions: string[] }>('/profiles/permissions');
  return res.data.permissions;
}

export async function createProfile(
  name: string,
  description: string,
  permissions: string[],
): Promise<number> {
  const res = await apiClient.post<{ id: number }>('/profiles', {
    name,
    description,
    permissions,
  });
  return res.data.id;
}

export async function updateProfile(
  id: number,
  description: string,
  permissions: string[],
): Promise<void> {
  await apiClient.patch(`/profiles/${id}`, { description, permissions });
}

export async function deleteProfile(id: number): Promise<void> {
  await apiClient.delete(`/profiles/${id}`);
}

export async function changeUserRole(userId: number, role: string): Promise<void> {
  await apiClient.patch(`/users/${userId}/role`, { role });
}

export async function assignUserProfile(
  userId: number,
  profileId: number | null,
): Promise<void> {
  await apiClient.patch(`/users/${userId}/profile`, { profile_id: profileId });
}
