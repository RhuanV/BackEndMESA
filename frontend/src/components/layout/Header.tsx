/**
 * Header — Top navigation bar for the Dashboard layout.
 *
 * Displays:
 * - Application title
 * - Current user info (non-sensitive: username and role only)
 * - Logout button
 * - Sidebar toggle for mobile
 */
import { useAuth } from '@/features/auth/hooks/useAuth';
import { Button, ThemeToggle } from '@/components/ui';
import { APP_NAME } from '@/lib/constants';

interface HeaderProps {
  readonly onToggleSidebar: () => void;
  readonly isSidebarOpen: boolean;
}

const roleLabels: Record<string, string> = {
  analyst: 'Analista',
  admin: 'Administrador',
  dev: 'Desenvolvedor',
};

export function Header({ onToggleSidebar, isSidebarOpen }: HeaderProps) {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    void logout();
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-neutral-200 bg-surface px-4 lg:px-6">
      {/* Left: hamburger + title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="rounded-lg p-2 text-neutral-500 hover:bg-neutral-100 hover:text-neutral-700 transition-colors lg:hidden"
          aria-label={isSidebarOpen ? 'Fechar menu' : 'Abrir menu'}
          aria-expanded={isSidebarOpen}
          type="button"
        >
          <svg
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            {isSidebarOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
        <h1 className="text-lg font-semibold text-primary-700 tracking-tight">
          {APP_NAME}
        </h1>
      </div>

      {/* Right: user info + logout */}
      <div className="flex items-center gap-2">
        {user && (
          <div className="hidden sm:flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-medium text-neutral-800">{user.username}</p>
              <p className="text-xs text-neutral-500">
                {roleLabels[user.role] ?? user.role}
              </p>
            </div>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-600 text-xs font-semibold text-white">
              {user.username.charAt(0).toUpperCase()}
            </div>
          </div>
        )}
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            aria-label="Sair do sistema"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9"
              />
            </svg>
            <span className="hidden sm:inline">Sair</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
