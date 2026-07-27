export type FormTab = 'basic' | 'discs' | 'covers' | 'archives';

export interface LocalCoverItem {
  id: string;
  base64: string;
  mimeType: string;
  fileName: string;
  fileSize: number;
  coverType: string;
  previewUrl: string;
}

export interface DraftCoverItem {
  id: string;
  base64: string;
  mimeType: string;
  fileName: string;
  fileSize: number;
  coverType: string;
}

export interface ArtistSeed {
  name_original?: string | null;
  name_translated?: string | null;
  role?: string | null;
}

export interface TrackSeed {
  track_number?: number | string | null;
  title_original?: string | null;
  title_translated?: string | null;
  duration_seconds?: number | string | null;
  audio_codec?: string | null;
  video_codec?: string | null;
  bit_depth?: number | string | null;
  sample_rate?: number | string | null;
  bitrate_kbps?: number | string | null;
  bitrate_mode?: string | null;
  is_instrumental?: boolean | null;
  artists?: ArtistSeed[] | null;
}

export interface DiscSeed {
  disc_number?: number | string | null;
  media_type?: string | null;
  container_format?: string | null;
  catalog_number?: string | null;
  log_type?: string | null;
  log_score?: number | string | null;
  raw_log_text?: string | null;
  raw_cue_text?: string | null;
  accuraterip_summary?: string | null;
  tracks?: TrackSeed[] | null;
}

export interface ArchiveLinkSeed {
  provider_name?: string | null;
  download_url?: string | null;
  is_active?: boolean | null;
}

export interface ArchiveSeed {
  archive_name?: string | null;
  encryption_password?: string | null;
  file_size_bytes?: number | string | null;
  hash_sha256?: string | null;
  links?: ArchiveLinkSeed[] | null;
}

export interface ExternalLinkSeed {
  site_name?: string | null;
  url?: string | null;
}

export interface AlbumFormRawValue {
  album_id?: string | null;
  title_original?: string | null;
  title_translated?: string | null;
  original_folder_name?: string | null;
  release_year?: number | string | null;
  release_month?: number | string | null;
  release_day?: number | string | null;
  label?: string | null;
  publisher?: string | null;
  storage_drive?: string | null;
  relative_path?: string | null;
  event_id?: string | null;
  franchise_id?: string | null;
  album_artist_id?: string | null;
  discs?: DiscSeed[] | null;
  archives?: ArchiveSeed[] | null;
  external_links?: ExternalLinkSeed[] | null;
}

export interface AlbumFormDraft {
  formValue: AlbumFormRawValue;
  coversList: DraftCoverItem[];
}
