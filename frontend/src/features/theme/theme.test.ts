import { describe, it, expect } from 'vitest';
import { nextTheme } from './types';

describe('nextTheme', () => {
  it('toggles light → dark', () => {
    expect(nextTheme('light')).toBe('dark');
  });

  it('toggles dark → light', () => {
    expect(nextTheme('dark')).toBe('light');
  });

  it('is its own inverse (two toggles return to start)', () => {
    expect(nextTheme(nextTheme('light'))).toBe('light');
    expect(nextTheme(nextTheme('dark'))).toBe('dark');
  });
});
