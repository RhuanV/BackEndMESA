import { describe, it, expect } from 'vitest';
import { resetPasswordSchema } from './resetPasswordSchema';

describe('resetPasswordSchema', () => {
  it('accepts a valid username + code + password', () => {
    const result = resetPasswordSchema.safeParse({
      username: 'alice',
      code: 'ABCD2345',
      newPassword: 'newpass12',
    });
    expect(result.success).toBe(true);
  });

  it('rejects a password shorter than 8 characters', () => {
    const result = resetPasswordSchema.safeParse({
      username: 'alice',
      code: 'ABCD2345',
      newPassword: 'short',
    });
    expect(result.success).toBe(false);
  });

  it('rejects a missing/short recovery code', () => {
    const result = resetPasswordSchema.safeParse({
      username: 'alice',
      code: '123',
      newPassword: 'newpass12',
    });
    expect(result.success).toBe(false);
  });
});
