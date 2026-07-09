import { describe, it, expect } from 'vitest';
import { hasPermission, ROLE_PERMISSIONS } from './auth';

describe('RBAC permissions (3-role model)', () => {
  it('defines exactly the three roles', () => {
    expect(Object.keys(ROLE_PERMISSIONS).sort()).toEqual([
      'administrador',
      'desenvolvedor',
      'operador',
    ]);
  });

  it('operador has operational perms but no admin or dev perms', () => {
    expect(hasPermission('operador', 'map:view')).toBe(true);
    expect(hasPermission('operador', 'analysis:run')).toBe(true);
    expect(hasPermission('operador', 'admin:users')).toBe(false);
    expect(hasPermission('operador', 'dev:health')).toBe(false);
  });

  it('administrador has admin perms but not developer tools', () => {
    expect(hasPermission('administrador', 'admin:users')).toBe(true);
    expect(hasPermission('administrador', 'admin:audit')).toBe(true);
    expect(hasPermission('administrador', 'dev:health')).toBe(false);
  });

  it('desenvolvedor has everything, including developer tools', () => {
    expect(hasPermission('desenvolvedor', 'admin:users')).toBe(true);
    expect(hasPermission('desenvolvedor', 'dev:health')).toBe(true);
    expect(hasPermission('desenvolvedor', 'dev:debug')).toBe(true);
  });
});
