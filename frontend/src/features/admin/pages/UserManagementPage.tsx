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
}

const roleBadgeColors: Record<UserRole, string> = {
  coordenador: 'bg-purple-100 text-purple-700',
  gestor: 'bg-amber-100 text-amber-700',
  supervisor: 'bg-blue-100 text-blue-700',
  operador: 'bg-emerald-100 text-emerald-700',
  administrador: 'bg-teal-100 text-teal-700',
};

const roleOptions: ReadonlyArray<{ value: UserRole; label: string }> = [
  { value: 'coordenador', label: 'Coordenador' },
  { value: 'gestor', label: 'Gestor' },
  { value: 'supervisor', label: 'Supervisor' },
  { value: 'operador', label: 'Operador' },
  { value: 'administrador', label: 'Administrador' },
];

export function UserManagementPage() {
  const { user } = useAuth();
  const canCreateUsers = user ? hasPermission(user.role, 'admin:users:create') : false;

  const [users, setUsers] = useState<UserRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<UserRole>('operador');
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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
    setIsSubmitting(true);
    try {
      await apiClient.post('/users/signup', null, {
        params: { username: newUsername.trim(), password: newPassword, role: newRole },
      });
      setFormSuccess(`Usuário "${newUsername.trim()}" criado.`);
      setNewUsername('');
      setNewPassword('');
      setNewRole('operador');
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
              onChange={(e) => setNewRole(e.target.value as UserRole)}
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
              {users.map((u) => (
                <tr key={u.id} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-neutral-900">{sanitize(u.username)}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${roleBadgeColors[u.role] ?? 'bg-neutral-100 text-neutral-700'}`}>
                      {sanitize(u.role)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-neutral-500">{u.created_at ?? '—'}</td>
                  <td className="px-4 py-3 text-right">
                    <Button variant="ghost" size="sm">Editar</Button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-neutral-400">Nenhum usuário encontrado.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
