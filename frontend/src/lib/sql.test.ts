import { describe, expect, it } from 'vitest';
import { isReadonlySelect } from './sql';

describe('isReadonlySelect', () => {
  it('accepts a single SELECT or WITH', () => {
    expect(isReadonlySelect('SELECT 1 FROM dual')).toBe(true);
    expect(isReadonlySelect('WITH t AS (SELECT 1) SELECT * FROM t')).toBe(true);
  });

  it('rejects DML and DDL', () => {
    for (const q of ['DELETE FROM x', 'INSERT INTO x VALUES (1)', 'DROP TABLE x', 'UPDATE x SET a=1', 'TRUNCATE TABLE x']) {
      expect(isReadonlySelect(q)).toBe(false);
    }
  });

  it('rejects stacked statements and empty input', () => {
    expect(isReadonlySelect('SELECT 1; DROP TABLE x')).toBe(false);
    expect(isReadonlySelect('')).toBe(false);
    expect(isReadonlySelect('   ')).toBe(false);
  });

  it('is not fooled by comments, and ignores keywords inside string literals', () => {
    expect(isReadonlySelect('SELECT 1 /* ok */ ; DELETE FROM x')).toBe(false);
    expect(isReadonlySelect("SELECT 'delete' FROM dual")).toBe(true);
  });
});
