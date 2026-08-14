import { FormControl } from '@angular/forms';
import { describe, expect, it } from 'vitest';
import { fuzzyDateValidator } from './fuzzy-date.validator';

describe('Fuzzy Date Validator', () => {
  const validator = fuzzyDateValidator();

  it('returns null for empty or whitespace values (optional field)', () => {
    expect(validator(new FormControl(''))).toBeNull();
    expect(validator(new FormControl('   '))).toBeNull();
    expect(validator(new FormControl(null))).toBeNull();
  });

  it('accepts valid full dates with slashes, dots, and dashes', () => {
    expect(validator(new FormControl('2024/08/15'))).toBeNull();
    expect(validator(new FormControl('2024.08.15'))).toBeNull();
    expect(validator(new FormControl('2024-08-15'))).toBeNull();
  });

  it('accepts valid year-only and fuzzy month/day wildcards', () => {
    expect(validator(new FormControl('2004'))).toBeNull();
    expect(validator(new FormControl('2004/08/xx'))).toBeNull();
    expect(validator(new FormControl('2004/xx/xx'))).toBeNull();
    expect(validator(new FormControl('1998.xx.xx'))).toBeNull();
    expect(validator(new FormControl('1998-10-XX'))).toBeNull();
  });

  it('rejects invalid year, month, or day formats', () => {
    expect(validator(new FormControl('abcd/01/01'))).toEqual({ invalidFuzzyDate: true });
    expect(validator(new FormControl('2024/13/01'))).toEqual({ invalidFuzzyDate: true });
    expect(validator(new FormControl('2024/00/01'))).toEqual({ invalidFuzzyDate: true });
    expect(validator(new FormControl('2024/08/32'))).toEqual({ invalidFuzzyDate: true });
    expect(validator(new FormControl('15-08-2024'))).toEqual({ invalidFuzzyDate: true });
  });
});
