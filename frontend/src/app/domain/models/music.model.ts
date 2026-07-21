export type LibraryCategory =
  | 'Rock'
  | 'Pop'
  | 'Electronic'
  | 'Classical'
  | 'Soundtrack'
  | 'GameOST'
  | 'Doujin'
  | 'Vocaloid'
  | 'Anime'
  | 'JPop'
  | 'VNs';

export type MediaType = 'CD' | 'DVD' | 'BD' | 'Cassette' | 'Vinyl' | 'Web';
export type ContainerFormat = 'Tracks' | 'ISO' | 'MDF' | 'BIN_CUE' | 'CDI' | 'IMG' | 'VOB';
export type LogType = 'EAC' | 'XLD' | 'EZCD' | 'CUERipper' | 'cyanrip' | 'whipper';
export type AudioCodec =
  'FLAC' | 'MP3' | 'ALAC' | 'AAC' | 'PCM' | 'AC3' | 'DTS' | 'WMA' | 'WavPack';

export interface TrackIngestPayload {
  track_number: number;
  title_original: string;
  title_translated?: string | null;
  duration_seconds?: number | null;
  audio_codec?: AudioCodec | null;
  bit_depth?: number | null;
  sample_rate?: number | null;
}

export interface DiscIngestPayload {
  disc_number: number;
  media_type: MediaType;
  container_format: ContainerFormat;
  catalog_number?: string | null;
  log_type?: LogType | null;
  log_score?: number | null;
  tracks: TrackIngestPayload[];
}

export interface ArchiveLinkIngestPayload {
  provider_name: string;
  download_url: string;
  is_active?: boolean;
}

export interface ArchiveIngestPayload {
  archive_name: string;
  encryption_password: string;
  file_size_bytes?: number | null;
  hash_sha256?: string | null;
  links: ArchiveLinkIngestPayload[];
}

export interface ExternalLinkIngestPayload {
  site_name: string;
  url: string;
  remote_item_id?: string | null;
}

export interface CoverIngestPayload {
  image_data: string;
  mime_type?: string;
  width?: number;
  height?: number;
}

export interface AlbumIngestRequest {
  title_original: string;
  categories: LibraryCategory[];
  original_folder_name: string;
  title_translated?: string | null;
  release_date?: string | null;
  label?: string | null;
  publisher?: string | null;
  storage_drive?: string | null;
  relative_path?: string | null;
  discs: DiscIngestPayload[];
  archives: ArchiveIngestPayload[];
  external_links: ExternalLinkIngestPayload[];
  cover?: CoverIngestPayload | null;
}

export interface AlbumIngestResponse {
  album_id: string;
  title_original: string;
  total_discs: number;
  total_tracks: number;
}

export interface AlbumSummary {
  id: string;
  title_original: string;
  title_translated: string | null;
  release_date: string | null;
  label: string | null;
  publisher: string | null;
  categories: LibraryCategory[];
  original_folder_name: string;
  total_discs: number;
  has_cover: boolean;
}

export interface PaginatedAlbumsResponse {
  items: AlbumSummary[];
  total_count: number;
  limit: number;
  offset: number;
}
