/**
 * UserManagementPage — Admin-only user management.
 * Protected by allowedRoles={['admin']} in the router.
 */
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api/axiosInstance';
import { sanitize } from '@/lib/security/sanitize';
import { Button } from '@/components/ui/Button';

interface UserRecord {
  readonly id: number;
  readonly username: string;
  readonly role: string;
  readonly created_at?: string;
}

const roleBadgeColors: Record<string, string> = {
  analyst: 'bg-blue-100 text-blue-700',
  admin: 'bg-purple-100 text-purple-700',
  dev: 'bg-teal-100 text-teal-700',
};

export function UserManagementPage() {
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await apiClient.get<UserRecord[]>('/users');
        setUsers(res.data);
      } catch {
        setError('Erro ao carregar usuários.');
      } finally {
        setIsLoading(false);
      }
    };
    void fetchUsers();
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900">Gestão de Usuários</h2>
          <p className="mt-1 text-sm text-neutral-500">Gerencie permissões e acessos do sistema.</p>
        </div>
        <Button size="sm">+ Novo Usuário</Button>
      </div>

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
