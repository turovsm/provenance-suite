import { describe, expect, it } from 'vitest';
import { stripMarkdown } from './markdown-cleaner';

describe('stripMarkdown', () => {
  it('returns empty string for null, undefined, or empty values', () => {
    expect(stripMarkdown(null)).toBe('');
    expect(stripMarkdown(undefined)).toBe('');
    expect(stripMarkdown('')).toBe('');
    expect(stripMarkdown('   ')).toBe('');
  });

  it('strips headers, bold, italics, and strikethroughs', () => {
    const input =
      '# Circle Biography\n**ZUN** is the *sole* member of ~~Team Alice~~ **Team Shanghai Alice**.';
    expect(stripMarkdown(input)).toBe(
      'Circle Biography ZUN is the sole member of Team Alice Team Shanghai Alice.',
    );
  });

  it('extracts link text and discards URL and image markup', () => {
    const input =
      'Check out [VGMdb Profile](https://vgmdb.net/artist/123) and ![Logo](https://img/logo.png).';
    expect(stripMarkdown(input)).toBe('Check out VGMdb Profile and Logo.');
  });

  it('strips blockquotes, lists, and code blocks', () => {
    const input =
      '> Official quote\n\n```js\nconsole.log(1);\n```\n- Item 1\n- Item 2\n1. Numbered';
    expect(stripMarkdown(input)).toBe('Official quote Item 1 Item 2 Numbered');
  });
});
