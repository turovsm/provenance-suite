export type MediaType = 'CD' | 'DVD' | 'BD' | 'Cassette' | 'Vinyl' | 'Web';
export type ContainerFormat = 'Tracks' | 'ISO' | 'MDF' | 'BIN_CUE' | 'CDI' | 'IMG' | 'VOB';
export type LogType = 'EAC' | 'XLD' | 'EZCD' | 'CUERipper' | 'cyanrip' | 'whipper';
export type AudioCodec =
  'FLAC' | 'MP3' | 'ALAC' | 'AAC' | 'PCM' | 'AC3' | 'DTS' | 'WMA' | 'WavPack';
export type VideoCodec = 'MPEG2' | 'H264' | 'HEVC' | 'VC1';
export type BitrateMode = 'CBR' | 'VBR' | 'ABR';

export interface MasterArtist {
  id: string;
  name_original: string;
  aliases: string[];
  image_url?: string | null;
  description?: string | null;
  created_at?: string | null;
}

export interface MasterFranchise {
  id: string;
  name_original: string;
  aliases: string[];
  franchise_type: string;
  image_url?: string | null;
  description?: string | null;
  created_at?: string | null;
}

export interface MasterLabel {
  id: string;
  name_original: string;
  aliases: string[];
  image_url?: string | null;
  description?: string | null;
  created_at?: string | null;
}

export interface MasterPublisher {
  id: string;
  name_original: string;
  aliases: string[];
  image_url?: string | null;
  description?: string | null;
  created_at?: string | null;
}

export type EntityTypeTag = 'artist' | 'franchise' | 'label' | 'publisher';

export interface EntitySummary {
  id: string;
  name_original: string;
  aliases: string[];
  entity_type: EntityTypeTag;
  image_url?: string | null;
  description?: string | null;
  franchise_type?: string | null;
  created_at?: string | null;
}

export interface PaginatedEntitiesResponse {
  items: EntitySummary[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface ArtistDiscography {
  artist_id: string;
  main_albums: AlbumSummary[];
  contribution_albums: AlbumSummary[];
}

export interface ArtistCreatePayload {
  name_original: string;
  aliases?: string[];
  description?: string | null;
  image_data?: string | null;
}

export interface ArtistUpdatePayload {
  name_original?: string | null;
  aliases?: string[];
  description?: string | null;
  image_data?: string | null;
}

export interface FranchiseCreatePayload {
  name_original: string;
  aliases?: string[];
  franchise_type?: string;
  description?: string | null;
  image_data?: string | null;
}

export interface FranchiseUpdatePayload {
  name_original?: string | null;
  aliases?: string[];
  franchise_type?: string | null;
  description?: string | null;
  image_data?: string | null;
}

export interface LabelCreatePayload {
  name_original: string;
  aliases?: string[];
  description?: string | null;
  image_data?: string | null;
}

export interface LabelUpdatePayload {
  name_original?: string | null;
  aliases?: string[];
  description?: string | null;
  image_data?: string | null;
}

export interface PublisherCreatePayload {
  name_original: string;
  aliases?: string[];
  description?: string | null;
  image_data?: string | null;
}

export interface PublisherUpdatePayload {
  name_original?: string | null;
  aliases?: string[];
  description?: string | null;
  image_data?: string | null;
}

export interface EventDateRange {
  start_date?: string | null;
  end_date?: string | null;
}

export interface MasterEvent {
  id: string;
  short_name: string;
  full_name: string | null;
  start_date: string | null;
  end_date: string | null;
  original_start_date?: string | null;
  original_end_date?: string | null;
  date_history?: EventDateRange[];
  additional_dates?: EventDateRange[];
  status: string;
}

export interface PaginatedEventsResponse {
  items: MasterEvent[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface EventCreatePayload {
  short_name: string;
  full_name?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  original_start_date?: string | null;
  original_end_date?: string | null;
  date_history?: EventDateRange[];
  additional_dates?: EventDateRange[];
  status?: string;
}

export interface EventUpdatePayload {
  short_name?: string | null;
  full_name?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  original_start_date?: string | null;
  original_end_date?: string | null;
  date_history?: EventDateRange[];
  additional_dates?: EventDateRange[];
  status?: string | null;
}

export interface ArtistIngestPayload {
  id?: string | null;
  name_original: string;
  role?: string;
}

export interface TrackIngestPayload {
  track_number: number;
  title_original: string;
  aliases?: string[];
  duration_seconds?: number | null;
  audio_codec?: AudioCodec | null;
  video_codec?: VideoCodec | null;
  bit_depth?: number | null;
  sample_rate?: number | null;
  bitrate_kbps?: number | null;
  bitrate_mode?: BitrateMode | null;
  is_instrumental?: boolean;
  artists?: ArtistIngestPayload[];
}

export interface DiscIngestPayload {
  disc_number: number;
  media_type: MediaType;
  container_format: ContainerFormat;
  catalog_number?: string | null;
  log_type?: LogType | null;
  log_score?: number | null;
  raw_log_text?: string | null;
  raw_cue_text?: string | null;
  accuraterip_summary?: string | null;
  tracks: TrackIngestPayload[];
}

export interface ArchiveLinkIngestPayload {
  provider_name: string;
  download_url: string;
  is_active?: boolean;
}

export interface ArchiveIngestPayload {
  archive_name: string;
  encryption_password?: string;
  file_size_bytes?: number | null;
  hash_sha256?: string | null;
  links: ArchiveLinkIngestPayload[];
}

export interface ExternalLinkIngestPayload {
  site_name: string;
  url: string;
}

export interface CoverIngestPayload {
  image_data: string;
  cover_type?: string;
}

export interface AlbumIngestRequest {
  album_id?: string | null;
  title_original: string;
  original_folder_name: string;
  aliases?: string[];
  release_year?: number | null;
  release_month?: number | null;
  release_day?: number | null;
  label?: string | null;
  publisher?: string | null;
  storage_drive?: string | null;
  relative_path?: string | null;
  event_id?: string | null;
  franchise_id?: string | null;
  album_artist_id?: string | null;
  album_artist?: ArtistIngestPayload | null;
  discs: DiscIngestPayload[];
  covers: CoverIngestPayload[];
  archives: ArchiveIngestPayload[];
  external_links: ExternalLinkIngestPayload[];
}

export interface AlbumIngestResponse {
  album_id: string;
  title_original: string;
  total_discs: number;
  total_tracks: number;
}

export interface ArtistDetailResponse {
  id: string;
  name_original: string;
  aliases: string[];
  role?: string;
  image_url?: string | null;
  description?: string | null;
}

export interface CoverResponse {
  id: string;
  storage_path: string;
  thumbhash: string | null;
  url: string;
  cover_type: string;
  created_at: string | null;
}

export interface AlbumSummary {
  id: string;
  title_original: string;
  aliases: string[];
  release_year: number | null;
  release_month: number | null;
  release_day: number | null;
  label: MasterLabel | string | null;
  publisher: MasterPublisher | string | null;
  original_folder_name: string;
  album_artist: ArtistDetailResponse | null;
  total_discs: number;
  covers: CoverResponse[];
}

export interface TrackDetailResponse {
  id: string;
  track_number: number;
  title_original: string;
  aliases: string[];
  duration_seconds: number | null;
  audio_codec: AudioCodec | null;
  video_codec?: VideoCodec | null;
  bit_depth: number | null;
  sample_rate: number | null;
  bitrate_kbps?: number | null;
  bitrate_mode?: BitrateMode | null;
  is_instrumental: boolean;
  artists?: ArtistDetailResponse[];
}

export interface DiscDetailResponse {
  id: string;
  disc_number: number;
  catalog_number: string | null;
  media_type: MediaType;
  container_format: ContainerFormat;
  log_type: LogType | null;
  log_score: number | null;
  raw_log_text: string | null;
  raw_cue_text: string | null;
  accuraterip_summary: string | null;
  tracks: TrackDetailResponse[];
}

export interface ArchiveLinkDetailResponse {
  id: string;
  provider_name: string;
  download_url: string;
  is_active: boolean;
}

export interface ArchiveDetailResponse {
  id: string;
  archive_name: string;
  encryption_password: string | null;
  file_size_bytes: number | null;
  hash_sha256: string | null;
  links: ArchiveLinkDetailResponse[];
}

export interface ExternalLinkDetailResponse {
  id: string;
  site_name: string;
  url: string;
}

export interface AlbumChangeEntry {
  type: 'added' | 'removed' | 'updated';
  old?: string;
  new?: string;
}

export interface AlbumChangelogResponse {
  id: string;
  user_id: string | null;
  action: string;
  changes: Record<string, AlbumChangeEntry>;
  created_at: string | null;
}

export interface AlbumDetailResponse {
  id: string;
  title_original: string;
  aliases: string[];
  release_year: number | null;
  release_month: number | null;
  release_day: number | null;
  label: MasterLabel | string | null;
  publisher: MasterPublisher | string | null;
  storage_drive?: string | null;
  relative_path?: string | null;
  event_id?: string | null;
  franchise_id?: string | null;
  original_folder_name: string;
  album_artist: ArtistDetailResponse | null;
  discs: DiscDetailResponse[];
  covers: CoverResponse[];
  archives: ArchiveDetailResponse[];
  external_links: ExternalLinkDetailResponse[];
  changelogs: AlbumChangelogResponse[];
}

export interface PaginatedAlbumsResponse {
  items: AlbumSummary[];
  total_count: number;
  limit: number;
  offset: number;
}
