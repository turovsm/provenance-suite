export interface DomainMapping {
  patterns: (string | RegExp)[];
  name: string;
}

const CLOUD_STORAGE_MAPPINGS: DomainMapping[] = [
  { patterns: ['mega.nz', 'mega.co.nz'], name: 'Mega' },
  { patterns: ['drive.google.com', 'docs.google.com'], name: 'Google Drive' },
  { patterns: ['disk.yandex.ru'], name: 'Yandex Disk' },
  { patterns: ['mediafire.com'], name: 'MediaFire' },
  { patterns: ['dropbox.com'], name: 'Dropbox' },
  { patterns: ['onedrive.live.com', '1drv.ms'], name: 'OneDrive' },
  { patterns: ['1fichier.com'], name: '1fichier' },
  { patterns: ['qiwi.gg'], name: 'Qiwi' },
  { patterns: ['pixeldrain.com'], name: 'Pixeldrain' },
  { patterns: ['pan.baidu.com'], name: 'Baidu Wangpan' },
  { patterns: ['terabox.com', 'freeterabox.com'], name: 'TeraBox' },
  { patterns: ['workupload.com'], name: 'WorkUpload' },
];

const EXTERNAL_INDEX_MAPPINGS: DomainMapping[] = [
  { patterns: ['vgmdb.net'], name: 'VGMdb' },
  { patterns: ['musicbrainz.org'], name: 'MusicBrainz' },
  { patterns: ['discogs.com'], name: 'Discogs' },
  { patterns: ['bandcamp.com'], name: 'Bandcamp' },
  { patterns: ['booth.pm'], name: 'BOOTH' },
  { patterns: ['vocadb.net'], name: 'VocaDB' },
  { patterns: ['utaitedb.net'], name: 'UtaiteDB' },
  { patterns: ['touhoudb.com'], name: 'TouhouDB' },
  { patterns: ['anidb.net'], name: 'AniDB' },
  { patterns: ['cdjapan.co.jp'], name: 'CDJapan' },
  { patterns: ['mora.jp'], name: 'Mora' },
  { patterns: ['ototoy.jp'], name: 'Ototoy' },
  { patterns: ['tower.jp', 'tower.com'], name: 'Tower Records' },
  { patterns: ['suruga-ya.jp', 'suruga-ya.com'], name: 'Suruga' },
  { patterns: ['hololivepro.com'], name: 'HololivePro' },
  { patterns: ['spotify.com'], name: 'Spotify' },
  { patterns: ['apple.com'], name: 'Apple Music' },
  { patterns: ['amazon.co.jp', 'amazon.com'], name: 'Amazon Music' },
  { patterns: ['deezer.com'], name: 'Deezer' },
  { patterns: ['qobuz.com'], name: 'Qobuz' },
  { patterns: ['tidal.com'], name: 'Tidal' },
  { patterns: ['youtube.com', 'youtu.be'], name: 'YouTube' },
];

function normalizeUnknownDomain(hostname: string): string {
  const cleanHost = hostname.replace(/^www\./i, '');
  const parts = cleanHost.split('.');

  if (parts.length === 0) return '';

  const mainSegment = parts.length >= 2 ? parts[parts.length - 2] : parts[0];

  return mainSegment
    .split(/[-_]/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join('-');
}

export function resolveDomainName(
  urlStr: string | null | undefined,
  type: 'cloud' | 'index',
): string | null {
  if (!urlStr || !urlStr.trim()) return null;

  let parsedUrl: URL;
  try {
    const formatted = /^https?:\/\//i.test(urlStr.trim())
      ? urlStr.trim()
      : `https://${urlStr.trim()}`;
    parsedUrl = new URL(formatted);
  } catch {
    return null;
  }

  const hostname = parsedUrl.hostname.toLowerCase();
  if (!hostname || !hostname.includes('.')) return null;

  const primaryMappings = type === 'cloud' ? CLOUD_STORAGE_MAPPINGS : EXTERNAL_INDEX_MAPPINGS;
  const secondaryMappings = type === 'cloud' ? EXTERNAL_INDEX_MAPPINGS : CLOUD_STORAGE_MAPPINGS;

  for (const entry of primaryMappings) {
    const matched = entry.patterns.some((pattern) =>
      typeof pattern === 'string'
        ? hostname === pattern || hostname.endsWith(`.${pattern}`)
        : pattern.test(hostname),
    );
    if (matched) return entry.name;
  }

  for (const entry of secondaryMappings) {
    const matched = entry.patterns.some((pattern) =>
      typeof pattern === 'string'
        ? hostname === pattern || hostname.endsWith(`.${pattern}`)
        : pattern.test(hostname),
    );
    if (matched) return entry.name;
  }

  return normalizeUnknownDomain(hostname);
}
