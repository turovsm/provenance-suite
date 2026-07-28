import { formatBytes } from './format-bytes';

describe('Format Bytes Utility', () => {
  it('returns empty string for null, undefined, or zero values', () => {
    expect(formatBytes(null)).toBe('');
    expect(formatBytes(undefined)).toBe('');
    expect(formatBytes(0)).toBe('');
  });

  it('formats byte quantities into human-readable strings with binary steps', () => {
    expect(formatBytes(512)).toBe('512 Bytes');
    expect(formatBytes(1024)).toBe('1 KB');
    expect(formatBytes(1572864)).toBe('1.5 MB');
    expect(formatBytes(1073741824)).toBe('1 GB');
  });
});
