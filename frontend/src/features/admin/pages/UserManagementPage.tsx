/**
 * UserManagementPage — System user management.
 *
 * Access (Router): administrador, desenvolvedor.
 * Creation form and recovery-code issuance are visible only for roles with the
 * `admin:users:create` permission (administrador and desenvolvedor).
 *
 * Defense in depth: the UI gate is cosmetic; the real security boundary
 * is at POST /users/signup, which validates the JWT role on the backend.
 */
import { useState, useEffect, useCallback } from 'react';
import type { FormEvent } from 'react';
import apiClient from '@/lib/api/axiosInstance';
import { extractErrorDetail } from '@/lib/api/errors';
import { sanitize } from '@/lib/security/sanitize';
import { getPasswordStrengthErrors } from '@/lib/validation/password';
import { Button, Input, Select } from '@/components/ui';
import { RecoveryCodeModal } from '@/features/admin/components/RecoveryCodeModal';
import { ResetPasswordModal } from '@/features/admin/components/ResetPasswordModal';
import { useAuth } from '@/features/auth/hooks/useAuth';
import {
  assignUserProfile,
  changeUserRole,
  listProfiles,
  type PermissionProfile,
} from '@/features/admin/services/profilesApi';
import { hasPermission } from '@/types';
import type { UserRole } from '@/types';

interface UserRecord {
  readonly id: number;
  readonly username: string;
  readonly role: UserRole;
  readonly created_at?: string;
  readonly is_protected?: boolean;
  readonly profile_id?: number | null;
  readonly profile_name?: string | null;
}

const roleBadgeColors: Record<UserRole, string> = {
  operador: 'bg-emerald-100 text-emerald-700',
  administrador: 'bg-teal-100 text-teal-700',
  desenvolvedor: 'bg-indigo-100 text-indigo-700',
};

const roleOptions: ReadonlyArray<{ value: UserRole; label: string }> = [
  { value: 'operador', label: 'Operador' },
  { value: 'administrador', label: 'Administrador' },
  { value: 'desenvolvedor', label: 'Desenvolvedor' },
];

export function UserManagementPage() {
  const { user } = useAuth();
  const canCreateUsers = user ? hasPermission(user.role, 'admin:users:create') : false;

  const [users, setUsers] = useState<UserRecord[]>([]);
  const [profiles, setProfiles] = useState<PermissionProfile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rowBusyId, setRowBusyId] = useState<number | null>(null);

  const [newUsername, setNewUsername] = useState('');
  const [newRole, setNewRole] = useState<UserRole | ''>('');
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Only a desenvolvedor may assign the privileged 'desenvolvedor' role; the UI
  // hides it for everyone else (the backend enforces the real boundary).
  const assignableRoles = roleOptions.filter(
    (o) => o.value !== 'desenvolvedor' || user?.role === 'desenvolvedor'
  );

  // Delete state
  const [deletingUserId, setDeletingUserId] = useState<number | null>(null);

  // Password reset state variables
  const [resetPasswordUserId, setResetPasswordUserId] = useState<number | null>(null);
  const [resetPasswordUsername, setResetPasswordUsername] = useState('');
  const [newResetPassword, setNewResetPassword] = useState('');
  const [resetPasswordError, setResetPasswordError] = useState<string | null>(null);
  const [isResetPasswordSubmitting, setIsResetPasswordSubmitting] = useState(false);
  const [resetPasswordSuccess, setResetPasswordSuccess] = useState<string | null>(null);

  // Recovery-code state (admin issues a single-use code to relay to the user)
  const [recoveryUserId, setRecoveryUserId] = useState<number | null>(null);
  const [recoveryUsername, setRecoveryUsername] = useState('');
  const [recoveryCode, setRecoveryCode] = useState<string | null>(null);
  const [recoveryExpiresAt, setRecoveryExpiresAt] = useState<string | null>(null);
  const [recoveryError, setRecoveryError] = useState<string | null>(null);
  const [isRecoverySubmitting, setIsRecoverySubmitting] = useState(false);
  const [recoveryCopied, setRecoveryCopied] = useState(false);

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
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data load on mount
    void fetchUsers();
  }, [fetchUsers]);

  useEffect(() => {
    if (!canCreateUsers) return;
    listProfiles()
      .then(setProfiles)
      .catch(() => setProfiles([]));
  }, [canCreateUsers]);

  const handleRoleChange = async (userId: number, role: UserRole) => {
    setRowBusyId(userId);
    setError(null);
    try {
      await changeUserRole(userId, role);
      await fetchUsers();
    } catch (err) {
      setError(extractErrorDetail(err) ?? 'Não foi possível alterar a role.');
    } finally {
      setRowBusyId(null);
    }
  };

  const handleProfileChange = async (userId: number, profileId: number | null) => {
    setRowBusyId(userId);
    setError(null);
    try {
      await assignUserProfile(userId, profileId);
      await fetchUsers();
    } catch (err) {
      setError(extractErrorDetail(err) ?? 'Não foi possível alterar o perfil.');
    } finally {
      setRowBusyId(null);
    }
  };

  const handleCreate = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormError(null);
    setFormSuccess(null);
    if (!newRole) {
      setFormError('Por favor, selecione um perfil.');
      return;
    }
    // First-access flow: the admin does not set a password. The backend creates
    // the account without a usable password and returns a single-use code the
    // user redeems on the login screen to set their own password.
    const created = newUsername.trim();
    setIsSubmitting(true);
    try {
      const res = await apiClient.post<{ id: number; code: string; expires_at: string }>(
        '/users/signup',
        null,
        { params: { username: created, role: newRole } }
      );
      setFormSuccess(`Usuário "${created}" criado. Repasse o código de primeiro acesso.`);
      setNewUsername('');
      setNewRole('');
      await fetchUsers();
      // Reuse the code modal to display the first-access code.
      setRecoveryUserId(res.data.id);
      setRecoveryUsername(created);
      setRecoveryCode(res.data.code);
      setRecoveryExpiresAt(res.data.expires_at);
      setRecoveryError(null);
      setRecoveryCopied(false);
    } catch (err) {
      const detail = extractErrorDetail(err);
      setFormError(detail ?? 'Não foi possível criar o usuário.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetPassword = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const passwordErrors = getPasswordStrengthErrors(newResetPassword);
    if (passwordErrors.length > 0) {
      setResetPasswordError(`A senha precisa de: ${passwordErrors.join(', ')}.`);
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
      const detail = extractErrorDetail(err);
      setResetPasswordError(detail ?? 'Não foi possível alterar a senha.');
    } finally {
      setIsResetPasswordSubmitting(false);
    }
  };

  const handleGenerateRecoveryCode = async (userId: number, username: string) => {
    setRecoveryUserId(userId);
    setRecoveryUsername(username);
    setRecoveryCode(null);
    setRecoveryExpiresAt(null);
    setRecoveryError(null);
    setRecoveryCopied(false);
    setIsRecoverySubmitting(true);
    try {
      const res = await apiClient.post<{ code: string; expires_at: string }>(
        `/users/${userId}/recovery-code`
      );
      setRecoveryCode(res.data.code);
      setRecoveryExpiresAt(res.data.expires_at);
    } catch (err) {
      setRecoveryError(extractErrorDetail(err) ?? 'Não foi possível gerar o código.');
    } finally {
      setIsRecoverySubmitting(false);
    }
  };

  const handleCopyRecoveryCode = () => {
    if (recoveryCode) {
      void navigator.clipboard?.writeText(recoveryCode);
      setRecoveryCopied(true);
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
        const detail = extractErrorDetail(err);
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
        <div className="mb-8 rounded-xl border border-neutral-200 bg-surface p-6 shadow-sm">
          <h3 className="mb-1 text-lg font-semibold text-neutral-900">Novo Usuário</h3>
          <p className="mb-4 text-sm text-neutral-500">
            A conta é criada sem senha. Ao salvar, um código de primeiro acesso é
            gerado para você repassar — o usuário define a própria senha na tela de login.
          </p>
          <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Usuário"
              type="text"
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
              required
              minLength={3}
              autoComplete="off"
            />
            <Select
              label="Perfil"
              options={assignableRoles}
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as UserRole | '')}
              required
            />
            <div className="sm:col-span-2 flex items-center justify-between gap-4">
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

      <div className="rounded-xl border border-neutral-200 bg-surface shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary-600 border-t-transparent" />
          </div>
        ) : (
          <table className="w-full text-sm" aria-label="Lista de usuários">
            <thead>
              <tr className="border-b border-neutral-200 bg-neutral-50">
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Usuário</th>
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Role</th>
                {canCreateUsers && (
                  <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Permissões</th>
                )}
                <th scope="col" className="px-4 py-3 text-left font-semibold text-neutral-700">Cadastro</th>
                <th scope="col" className="px-4 py-3 text-right font-semibold text-neutral-700">Ações</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-neutral-900">{sanitize(u.username)}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${roleBadgeColors[u.role] ?? 'bg-neutral-100 text-neutral-700'}`}>
                      {sanitize(u.role)}
                    </span>
                  </td>
                  {canCreateUsers && (
                    <td className="px-4 py-3">
                      {u.is_protected ? (
                        <span className="text-xs text-neutral-400">protegido</span>
                      ) : (
                        <div className="flex flex-col gap-1.5">
                          <select
                            aria-label={`Role de ${u.username}`}
                            className="rounded border border-neutral-300 bg-surface px-2 py-1 text-xs"
                            value={u.role}
                            disabled={rowBusyId === u.id || u.username === user?.username}
                            onChange={(e) => void handleRoleChange(u.id, e.target.value as UserRole)}
                          >
                            {assignableRoles.map((o) => (
                              <option key={o.value} value={o.value}>{o.label}</option>
                            ))}
                          </select>
                          <select
                            aria-label={`Perfil de ${u.username}`}
                            className="rounded border border-neutral-300 bg-surface px-2 py-1 text-xs"
                            value={u.profile_id ?? ''}
                            disabled={rowBusyId === u.id}
                            onChange={(e) =>
                              void handleProfileChange(u.id, e.target.value ? Number(e.target.value) : null)
                            }
                          >
                            <option value="">Sem perfil</option>
                            {profiles.map((p) => (
                              <option key={p.id} value={p.id}>{p.name}</option>
                            ))}
                          </select>
                        </div>
                      )}
                    </td>
                  )}
                  <td className="px-4 py-3 text-neutral-500">{u.created_at ?? '—'}</td>
                  <td className="px-4 py-3 text-right">
                    {canCreateUsers ? (
                      <div className="flex justify-end gap-2">
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
                          className="text-primary-600 hover:text-primary-700 hover:bg-primary-50"
                          onClick={() => void handleGenerateRecoveryCode(u.id, u.username)}
                          disabled={deletingUserId !== null || u.is_protected}
                        >
                          Código
                        </Button>
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
                </tr>
              ))}
              {users.length === 0 && (
                <tr><td colSpan={canCreateUsers ? 5 : 4} className="px-4 py-8 text-center text-neutral-400">Nenhum usuário encontrado.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {resetPasswordUserId !== null && (
        <ResetPasswordModal
          username={resetPasswordUsername}
          newPassword={newResetPassword}
          onNewPasswordChange={setNewResetPassword}
          error={resetPasswordError}
          success={resetPasswordSuccess}
          isSubmitting={isResetPasswordSubmitting}
          onSubmit={handleResetPassword}
          onClose={() => setResetPasswordUserId(null)}
        />
      )}

      {recoveryUserId !== null && (
        <RecoveryCodeModal
          username={recoveryUsername}
          code={recoveryCode}
          expiresAt={recoveryExpiresAt}
          error={recoveryError}
          isSubmitting={isRecoverySubmitting}
          copied={recoveryCopied}
          onCopy={handleCopyRecoveryCode}
          onClose={() => setRecoveryUserId(null)}
        />
      )}
    </div>
  );
}
