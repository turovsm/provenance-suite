import { describe, expect, it } from 'vitest';
import { resolveDomainName } from './domain-resolver';

describe('Domain Resolver Utility', () => {
  it('returns null for empty, null, or whitespace-only inputs', () => {
    expect(resolveDomainName(null, 'cloud')).toBeNull();
    expect(resolveDomainName(undefined, 'cloud')).toBeNull();
    expect(resolveDomainName('', 'cloud')).toBeNull();
    expect(resolveDomainName('   ', 'cloud')).toBeNull();
  });

  it('returns null for strings without valid domain format', () => {
    expect(resolveDomainName('not-a-url', 'cloud')).toBeNull();
    expect(resolveDomainName('localhost', 'cloud')).toBeNull();
  });

  it('resolves known cloud storage domains', () => {
    expect(resolveDomainName('https://mega.nz/file/abc123', 'cloud')).toBe('Mega');
    expect(resolveDomainName('https://drive.google.com/drive/folders/xyz', 'cloud')).toBe(
      'Google Drive',
    );
    expect(resolveDomainName('https://mediafire.com/file/123', 'cloud')).toBe('MediaFire');
    expect(resolveDomainName('https://1fichier.com/?abc', 'cloud')).toBe('1fichier');
    expect(resolveDomainName('https://pixeldrain.com/u/abc', 'cloud')).toBe('Pixeldrain');
  });

  it('resolves known external index and music database domains', () => {
    expect(resolveDomainName('https://vgmdb.net/album/1024', 'index')).toBe('VGMdb');
    expect(resolveDomainName('https://musicbrainz.org/release/123', 'index')).toBe('MusicBrainz');
    expect(resolveDomainName('https://discogs.com/release/123', 'index')).toBe('Discogs');
    expect(resolveDomainName('https://circle.bandcamp.com/album/ost', 'index')).toBe('Bandcamp');
    expect(resolveDomainName('https://booth.pm/ja/items/123', 'index')).toBe('BOOTH');
    expect(resolveDomainName('https://vocadb.net/Al/123', 'index')).toBe('VocaDB');
    expect(resolveDomainName('https://youtu.be/abc123', 'index')).toBe('YouTube');
  });

  it('formats unknown domains into normalized Title-Case labels', () => {
    expect(resolveDomainName('https://mirror.custom-archive.org/file.zip', 'cloud')).toBe(
      'Custom-Archive',
    );
    expect(resolveDomainName('https://sub.doujin-music.jp/download', 'cloud')).toBe('Doujin-Music');
  });

  it('tolerates URLs without explicit protocol prefix', () => {
    expect(resolveDomainName('mega.nz/file/123', 'cloud')).toBe('Mega');
    expect(resolveDomainName('vgmdb.net/album/55', 'index')).toBe('VGMdb');
  });
});
