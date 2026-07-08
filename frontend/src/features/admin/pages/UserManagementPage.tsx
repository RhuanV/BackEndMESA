/**
 * UserManagementPage — Gestão de usuários do sistema (Sprint 3).
 *
 * Acesso (Router): coordenador, gestor, supervisor.
 * Form de criação: visível apenas para perfis com permission
 * `admin:users:create` (coordenador e supervisor).
 *
 * Defense in depth: o gate na UI é cosmético; a fronteira de segurança real
 * fica em POST /users/signup, que valida o role do JWT no back.
 */
import { useState, useEffect, useCallback } from 'react';
import type { FormEvent } from 'react';
import apiClient from '@/lib/api/axiosInstance';
import { sanitize } from '@/lib/security/sanitize';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { hasPermission } from '@/types/auth';
import type { UserRole } from '@/types/auth';

interface UserRecord {
  readonly id: number;
  readonly username: string;
  readonly role: UserRole;
  readonly created_at?: string;
  readonly is_protected?: boolean;
}

const roleBadgeColors: Record<UserRole, string> = {
  coordenador: 'bg-purple-100 text-purple-700',
  gestor: 'bg-amber-100 text-amber-700',
  supervisor: 'bg-blue-100 text-blue-700',
  operador: 'bg-emerald-100 text-emerald-700',
  administrador: 'bg-teal-100 text-teal-700',
  desenvolvedor: 'bg-indigo-100 text-indigo-700',
};

const roleOptions: ReadonlyArray<{ value: UserRole; label: string }> = [
  { value: 'coordenador', label: 'Coordenador' },
  { value: 'gestor', label: 'Gestor' },
  { value: 'supervisor', label: 'Supervisor' },
  { value: 'operador', label: 'Operador' },
  { value: 'administrador', label: 'Administrador' },
  { value: 'desenvolvedor', label: 'Desenvolvedor' },
];

export function UserManagementPage() {
  const { user } = useAuth();
  const canCreateUsers = user ? hasPermission(user.role, 'admin:users:create') : false;

  const [users, setUsers] = useState<UserRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<UserRole | ''>('');
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Edit/Delete state variables
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editingUsername, setEditingUsername] = useState('');
  const [editError, setEditError] = useState<string | null>(null);
  const [isEditingSubmitting, setIsEditingSubmitting] = useState(false);
  const [deletingUserId, setDeletingUserId] = useState<number | null>(null);

  // Password reset state variables
  const [resetPasswordUserId, setResetPasswordUserId] = useState<number | null>(null);
  const [resetPasswordUsername, setResetPasswordUsername] = useState('');
  const [newResetPassword, setNewResetPassword] = useState('');
  const [resetPasswordError, setResetPasswordError] = useState<string | null>(null);
  const [isResetPasswordSubmitting, setIsResetPasswordSubmitting] = useState(false);
  const [resetPasswordSuccess, setResetPasswordSuccess] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    try {
      const res = await apiClient.get<UserRecord[]>('/users');
      setUsers(res.data);
      setError(null);
    } catch {
      setError('Erro ao carregar usuários.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchUsers();
  }, [fetchUsers]);

  const handleCreate = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormError(null);
    setFormSuccess(null);
    if (!newRole) {
      setFormError('Por favor, selecione um perfil.');
      return;
    }
    setIsSubmitting(true);
    try {
      await apiClient.post('/users/signup', null, {
        params: { username: newUsername.trim(), password: newPassword, role: newRole },
      });
      setFormSuccess(`Usuário "${newUsername.trim()}" criado.`);
      setNewUsername('');
      setNewPassword('');
      setNewRole('');
      await fetchUsers();
    } catch (err) {
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setFormError(detail ?? 'Não foi possível criar o usuário.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = async (userId: number) => {
    const trimmedUsername = editingUsername.trim();
    if (!trimmedUsername) {
      setEditError('O nome de usuário não pode ser vazio.');
      return;
    }
    setEditError(null);
    setIsEditingSubmitting(true);
    try {
      await apiClient.put(`/users/${userId}/username`, {
        username: trimmedUsername,
      });
      setEditingUserId(null);
      await fetchUsers();
    } catch (err) {
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setEditError(detail ?? 'Não foi possível alterar o nome do usuário.');
    } finally {
      setIsEditingSubmitting(false);
    }
  };

  const handleResetPassword = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (newResetPassword.length < 6) {
      setResetPasswordError('A nova senha deve ter pelo menos 6 caracteres.');
      return;
    }
    setResetPasswordError(null);
    setResetPasswordSuccess(null);
    setIsResetPasswordSubmitting(true);
    try {
      await apiClient.put(`/users/${resetPasswordUserId}/password`, {
        new_password: newResetPassword,
      });
      setResetPasswordSuccess('Senha redefinida com sucesso!');
      setNewResetPassword('');
      setTimeout(() => {
        setResetPasswordUserId(null);
        setResetPasswordSuccess(null);
      }, 1500);
    } catch (err) {
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setResetPasswordError(detail ?? 'Não foi possível alterar a senha.');
    } finally {
      setIsResetPasswordSubmitting(false);
    }
  };

  const handleDelete = async (userId: number, username: string) => {
    if (window.confirm(`Tem certeza de que deseja excluir o usuário "${username}"?`)) {
      setDeletingUserId(userId);
      setError(null);
      try {
        await apiClient.delete(`/users/${userId}`);
        await fetchUsers();
      } catch (err) {
        const detail =
          err && typeof err === 'object' && 'response' in err
            ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
            : undefined;
        setError(detail ?? 'Não foi possível excluir o usuário.');
      } finally {
        setDeletingUserId(null);
      }
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-neutral-900">Gestão de Usuários</h2>
        <p className="mt-1 text-sm text-neutral-500">Gerencie permissões e acessos do sistema.</p>
      </div>

      {canCreateUsers && (
        <div className="mb-8 rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-semibold text-neutral-900">Novo Usuário</h3>
          <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-3">
            <Input
              label="Usuário"
              type="text"
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
              required
              minLength={3}
              autoComplete="off"
            />
            <Input
              label="Senha"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={6}
              autoComplete="new-password"
            />
            <Select
              label="Perfil"
              options={roleOptions}
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as UserRole | '')}
              required
            />
            <div className="sm:col-span-3 flex items-center justify-between gap-4">
              <div className="text-sm" aria-live="polite">
                {formError && <p role="alert" className="text-danger-600">{formError}</p>}
                {formSuccess && <p className="text-emerald-600">{formSuccess}</p>}
              </div>
              <Button type="submit" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Criando...' : 'Criar Usuário'}
              </Button>
            </div>
          </form>
        </div>
      )}

      {error && (
        <div role="alert" className="mb-4 rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-600">{error}</div>
      )}

      <div className="rounded-xl border border-neutral-200 bg-white shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
          </div>
        ) : (
          <table className="w-full text-sm" aria-label="Lista de usuários">
            <thead>
              <tr className="border-b border-neutral-200 bg-neutral-50">
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Usuário</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Perfil</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Cadastro</th>
                <th scope="col" className="px-4 py-3 text-right font-semibold text-neutral-700">Ações</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const isEditing = editingUserId === u.id;
                return (
                  <tr key={u.id} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors">
                    {isEditing ? (
                      <>
                        <td className="px-4 py-3 font-medium text-neutral-900" colSpan={2}>
                          <div className="flex flex-col gap-1">
                            <input
                              type="text"
                              value={editingUsername}
                              onChange={(e) => setEditingUsername(e.target.value)}
                              required
                              minLength={3}
                              className="w-full max-w-[240px] rounded-lg border border-neutral-300 px-3 py-1.5 text-sm text-neutral-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:bg-neutral-100 disabled:text-neutral-400"
                              aria-label="Editar nome de usuário"
                              disabled={isEditingSubmitting}
                            />
                            {editError && <p role="alert" className="text-xs text-danger-600 font-normal">{editError}</p>}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-neutral-500">{u.created_at ?? '—'}</td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => void handleEdit(u.id)}
                              isLoading={isEditingSubmitting}
                            >
                              Salvar
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setEditingUserId(null);
                                setEditError(null);
                              }}
                              disabled={isEditingSubmitting}
                            >
                              Cancelar
                            </Button>
                          </div>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="px-4 py-3 font-medium text-neutral-900">{sanitize(u.username)}</td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${roleBadgeColors[u.role] ?? 'bg-neutral-100 text-neutral-700'}`}>
                            {sanitize(u.role)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-neutral-500">{u.created_at ?? '—'}</td>
                        <td className="px-4 py-3 text-right">
                          {canCreateUsers ? (
                            <div className="flex justify-end gap-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setEditingUserId(u.id);
                                  setEditingUsername(u.username);
                                  setEditError(null);
                                }}
                                disabled={deletingUserId !== null || u.is_protected}
                              >
                                Editar
                              </Button>
                              {user?.role === 'desenvolvedor' && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="text-primary-600 hover:text-primary-700 hover:bg-primary-50"
                                  onClick={() => {
                                    setResetPasswordUserId(u.id);
                                    setResetPasswordUsername(u.username);
                                    setNewResetPassword('');
                                    setResetPasswordError(null);
                                    setResetPasswordSuccess(null);
                                  }}
                                  disabled={deletingUserId !== null || u.is_protected}
                                >
                                  Senha
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-danger-600 hover:text-danger-700 hover:bg-danger-50"
                                onClick={() => void handleDelete(u.id, u.username)}
                                isLoading={deletingUserId === u.id}
                                disabled={deletingUserId !== null || u.username === user?.username || u.is_protected}
                              >
                                Excluir
                              </Button>
                            </div>
                          ) : (
                            <span className="text-neutral-400">—</span>
                          )}
                        </td>
                      </>
                    )}
                  </tr>
                );
              })}
              {users.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-neutral-400">Nenhum usuário encontrado.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {resetPasswordUserId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-neutral-900/40 p-4 backdrop-blur-sm animate-fade-in" role="dialog" aria-modal="true">
          <div className="w-full max-w-md rounded-xl border border-neutral-200 bg-white p-6 shadow-xl animate-scale-in">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-neutral-900">
                Alterar Senha de {sanitize(resetPasswordUsername)}
              </h3>
              <button
                type="button"
                className="text-neutral-400 hover:text-neutral-600 transition-colors"
                onClick={() => setResetPasswordUserId(null)}
                aria-label="Fechar"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleResetPassword} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-neutral-700 block mb-1.5">
                  Senha Atual
                </label>
                <input
                  type="password"
                  value="••••••••"
                  disabled
                  className="w-full rounded-lg border border-neutral-300 bg-neutral-100 px-4 py-2 text-sm text-neutral-400 cursor-not-allowed select-none"
                  aria-label="Senha atual oculta"
                />
                <span className="text-xs text-neutral-400 mt-1 block">A senha atual é protegida e não pode ser revelada.</span>
              </div>

              <div>
                <label htmlFor="new-reset-password" className="text-sm font-medium text-neutral-700 block mb-1.5">
                  Nova Senha
                </label>
                <input
                  id="new-reset-password"
                  type="password"
                  value={newResetPassword}
                  onChange={(e) => setNewResetPassword(e.target.value)}
                  required
                  minLength={6}
                  autoComplete="new-password"
                  placeholder="Mínimo 6 caracteres"
                  className="w-full rounded-lg border border-neutral-300 px-4 py-2 text-sm text-neutral-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:bg-neutral-100 disabled:text-neutral-400"
                  disabled={isResetPasswordSubmitting || resetPasswordSuccess !== null}
                />
              </div>

              {resetPasswordError && (
                <div role="alert" className="text-sm text-danger-600 animate-fade-in">
                  {resetPasswordError}
                </div>
              )}

              {resetPasswordSuccess && (
                <div className="text-sm text-emerald-600 animate-fade-in">
                  {resetPasswordSuccess}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <Button
                  variant="ghost"
                  type="button"
                  onClick={() => setResetPasswordUserId(null)}
                  disabled={isResetPasswordSubmitting}
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  isLoading={isResetPasswordSubmitting}
                  disabled={resetPasswordSuccess !== null}
                >
                  Confirmar
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
