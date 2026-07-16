/**
 * ProfilesManagementPage — CRUD for custom permission profiles (Perfis).
 *
 * Access (Router): administrador, desenvolvedor. Backend gates every write on
 * the `admin:profiles` permission (defense in depth). System profiles (seeded
 * from the base roles) are read-only.
 */
import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';

import { Button, Input } from '@/components/ui';
import { extractErrorDetail } from '@/lib/api/errors';
import { sanitize } from '@/lib/security/sanitize';
import {
  createProfile,
  deleteProfile,
  listPermissionCatalog,
  listProfiles,
  updateProfile,
  type PermissionProfile,
} from '@/features/admin/services/profilesApi';

export function ProfilesManagementPage() {
  const [profiles, setProfiles] = useState<PermissionProfile[]>([]);
  const [catalog, setCatalog] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form state (shared for create and edit; editingId === null means create).
  const [editingId, setEditingId] = useState<number | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedPerms, setSelectedPerms] = useState<Set<string>>(new Set());
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      const [profs, cat] = await Promise.all([listProfiles(), listPermissionCatalog()]);
      setProfiles(profs);
      setCatalog(cat);
      setError(null);
    } catch (err) {
      setError(extractErrorDetail(err) ?? 'Erro ao carregar perfis.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data load on mount
    void load();
  }, [load]);

  const resetForm = () => {
    setEditingId(null);
    setName('');
    setDescription('');
    setSelectedPerms(new Set());
    setFormError(null);
  };

  const startEdit = (profile: PermissionProfile) => {
    setEditingId(profile.id);
    setName(profile.name);
    setDescription(profile.description ?? '');
    setSelectedPerms(new Set(profile.permissions));
    setFormError(null);
  };

  const togglePerm = (perm: string) => {
    setSelectedPerms((prev) => {
      const next = new Set(prev);
      if (next.has(perm)) next.delete(perm);
      else next.add(perm);
      return next;
    });
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);
    try {
      const perms = [...selectedPerms];
      if (editingId === null) {
        await createProfile(name.trim(), description.trim(), perms);
      } else {
        await updateProfile(editingId, description.trim(), perms);
      }
      resetForm();
      await load();
    } catch (err) {
      setFormError(extractErrorDetail(err) ?? 'Não foi possível salvar o perfil.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (profile: PermissionProfile) => {
    if (!window.confirm(`Excluir o perfil "${profile.name}"?`)) return;
    setError(null);
    try {
      await deleteProfile(profile.id);
      if (editingId === profile.id) resetForm();
      await load();
    } catch (err) {
      setError(extractErrorDetail(err) ?? 'Não foi possível excluir o perfil.');
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">Perfis de Permissão</h2>
        <p className="mt-1 text-sm text-neutral-500">
          Crie perfis customizados que concedem permissões adicionais sobre a role base.
        </p>
      </div>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600"
        >
          {error}
        </div>
      )}

      <div className="mb-8 rounded-xl border border-neutral-200 bg-surface p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-neutral-900">
          {editingId === null ? 'Novo Perfil' : `Editar Perfil`}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Nome"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              minLength={1}
              disabled={editingId !== null}
              autoComplete="off"
            />
            <Input
              label="Descrição"
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              autoComplete="off"
            />
          </div>

          <fieldset className="rounded-lg border border-neutral-200 p-4">
            <legend className="px-1 text-xs font-bold uppercase tracking-wider text-neutral-400">
              Permissões
            </legend>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {catalog.map((perm) => (
                <label key={perm} className="flex items-center gap-2 text-sm text-neutral-700">
                  <input
                    type="checkbox"
                    checked={selectedPerms.has(perm)}
                    onChange={() => togglePerm(perm)}
                    className="rounded border-neutral-300"
                  />
                  <span className="font-mono text-xs">{perm}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="flex items-center justify-between gap-4">
            <div className="text-sm" aria-live="polite">
              {formError && (
                <p role="alert" className="text-danger-600">
                  {formError}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              {editingId !== null && (
                <Button type="button" variant="ghost" size="sm" onClick={resetForm}>
                  Cancelar
                </Button>
              )}
              <Button type="submit" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Salvando...' : editingId === null ? 'Criar Perfil' : 'Salvar'}
              </Button>
            </div>
          </div>
        </form>
      </div>

      <div className="overflow-hidden rounded-xl border border-neutral-200 bg-surface shadow-sm">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
          </div>
        ) : (
          <table className="w-full text-sm" aria-label="Lista de perfis">
            <thead>
              <tr className="border-b border-neutral-200 bg-neutral-50">
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">
                  Perfil
                </th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">
                  Permissões
                </th>
                <th scope="col" className="px-4 py-3 text-right font-semibold text-neutral-700">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody>
              {profiles.map((p) => (
                <tr key={p.id} className="border-b border-neutral-100 hover:bg-neutral-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-neutral-900">{sanitize(p.name)}</div>
                    {p.description && (
                      <div className="text-xs text-neutral-500">{sanitize(p.description)}</div>
                    )}
                    {p.is_system && (
                      <span className="mt-1 inline-flex rounded-full bg-neutral-100 px-2 py-0.5 text-[10px] font-semibold text-neutral-500">
                        sistema
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-neutral-500">{p.permissions.length}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-primary-600 hover:bg-primary-50"
                        onClick={() => startEdit(p)}
                        disabled={p.is_system}
                      >
                        Editar
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-danger-600 hover:bg-danger-50"
                        onClick={() => void handleDelete(p)}
                        disabled={p.is_system}
                      >
                        Excluir
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {profiles.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-neutral-400">
                    Nenhum perfil encontrado.
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
