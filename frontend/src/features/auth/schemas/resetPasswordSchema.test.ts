import { describe, it, expect } from 'vitest';
import { resetPasswordSchema } from './resetPasswordSchema';

// A valid 20-character recovery code (unambiguous alphabet).
const VALID_CODE = 'ABCD2345EFGH6789JKLM';

describe('resetPasswordSchema', () => {
  it('accepts a valid username + code + strong password', () => {
    const result = resetPasswordSchema.safeParse({
      username: 'alice',
      code: VALID_CODE,
      newPassword: 'NewPass@12',
    });
    expect(result.success).toBe(true);
  });

  it('rejects a weak password (no uppercase/special)', () => {
    const result = resetPasswordSchema.safeParse({
      username: 'alice',
      code: VALID_CODE,
      newPassword: 'newpass12',
    });
    expect(result.success).toBe(false);
  });

  it('rejects a password shorter than 8 characters', () => {
    const result = resetPasswordSchema.safeParse({
      username: 'alice',
      code: VALID_CODE,
      newPassword: 'Ab@1',
    });
    expect(result.success).toBe(false);
  });

  it('rejects a recovery code that is not 20 characters', () => {
    const result = resetPasswordSchema.safeParse({
      username: 'alice',
      code: 'ABCD2345',
      newPassword: 'NewPass@12',
    });
    expect(result.success).toBe(false);
  });
});
