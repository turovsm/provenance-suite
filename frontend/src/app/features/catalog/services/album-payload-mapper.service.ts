import { Injectable } from '@angular/core';
import {
  AlbumIngestRequest,
  ArchiveIngestPayload,
  ArchiveLinkIngestPayload,
  AudioCodec,
  BitrateMode,
  ContainerFormat,
  DiscIngestPayload,
  ExternalLinkIngestPayload,
  LogType,
  MediaType,
  TrackIngestPayload,
  VideoCodec,
} from '../../../domain/models/music.model';
import {
  AlbumFormRawValue,
  ArchiveLinkSeed,
  ArchiveSeed,
  DiscSeed,
  ExternalLinkSeed,
  LocalCoverItem,
  TrackSeed,
} from '../models/album-form.model';

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function toNumberOrNull(value: unknown): number | null {
  return value !== null && value !== undefined && value !== '' ? Number(value) : null;
}

@Injectable({ providedIn: 'root' })
export class AlbumPayloadMapperService {
  toIngestRequest(formVal: AlbumFormRawValue, covers: LocalCoverItem[]): AlbumIngestRequest {
    const artistVal = formVal.album_artist_id;
    const isArtistUuid = typeof artistVal === 'string' && UUID_PATTERN.test(artistVal);

    return {
      album_id: formVal.album_id || null,
      title_original: formVal.title_original ?? '',
      title_translated: formVal.title_translated || null,
      original_folder_name: formVal.original_folder_name ?? '',
      release_year: toNumberOrNull(formVal.release_year),
      release_month: toNumberOrNull(formVal.release_month),
      release_day: toNumberOrNull(formVal.release_day),
      label: formVal.label || null,
      publisher: formVal.publisher || null,
      storage_drive: formVal.storage_drive || null,
      relative_path: formVal.relative_path || null,
      event_id: formVal.event_id || null,
      franchise_id: formVal.franchise_id || null,
      album_artist_id: isArtistUuid ? artistVal : null,
      album_artist: !isArtistUuid && artistVal ? { name_original: artistVal } : null,
      discs: (formVal.discs ?? []).map((d) => this.mapDisc(d)),
      archives: (formVal.archives ?? []).map((a) => this.mapArchive(a)),
      external_links: (formVal.external_links ?? []).map((el) => this.mapExternalLink(el)),
      covers: covers
        .filter((c) => Boolean(c.base64))
        .map((c) => ({ image_data: c.base64, cover_type: c.coverType })),
    };
  }

  private mapDisc(d: DiscSeed): DiscIngestPayload {
    return {
      disc_number: toNumberOrNull(d.disc_number) ?? 1,
      media_type: (d.media_type ?? 'CD') as MediaType,
      container_format: (d.container_format ?? 'Tracks') as ContainerFormat,
      catalog_number: d.catalog_number || null,
      log_type: (d.log_type as LogType) || null,
      log_score: toNumberOrNull(d.log_score),
      raw_log_text: d.raw_log_text || null,
      raw_cue_text: d.raw_cue_text || null,
      accuraterip_summary: d.accuraterip_summary || null,
      tracks: (d.tracks ?? []).map((t, tIdx) => this.mapTrack(t, tIdx)),
    };
  }

  private mapTrack(t: TrackSeed, index: number): TrackIngestPayload {
    return {
      track_number: index + 1,
      title_original: t.title_original ?? '',
      title_translated: t.title_translated || null,
      duration_seconds: toNumberOrNull(t.duration_seconds),
      audio_codec: (t.audio_codec as AudioCodec) || null,
      video_codec: (t.video_codec as VideoCodec) || null,
      bit_depth: toNumberOrNull(t.bit_depth),
      sample_rate: toNumberOrNull(t.sample_rate),
      bitrate_kbps: toNumberOrNull(t.bitrate_kbps),
      bitrate_mode: (t.bitrate_mode as BitrateMode) || null,
      is_instrumental: Boolean(t.is_instrumental),
      artists: (t.artists ?? []).map((ta) => ({
        name_original: ta.name_original ?? '',
        name_translated: ta.name_translated || null,
        role: ta.role ?? 'Composer',
      })),
    };
  }

  private mapArchive(a: ArchiveSeed): ArchiveIngestPayload {
    return {
      archive_name: a.archive_name ?? '',
      encryption_password: a.encryption_password || '',
      file_size_bytes: toNumberOrNull(a.file_size_bytes),
      hash_sha256: a.hash_sha256 || null,
      links: (a.links ?? []).map((lnk) => this.mapArchiveLink(lnk)),
    };
  }

  private mapArchiveLink(lnk: ArchiveLinkSeed): ArchiveLinkIngestPayload {
    return {
      provider_name: lnk.provider_name ?? '',
      download_url: lnk.download_url ?? '',
      is_active: Boolean(lnk.is_active),
    };
  }

  private mapExternalLink(el: ExternalLinkSeed): ExternalLinkIngestPayload {
    return {
      site_name: el.site_name ?? '',
      url: el.url ?? '',
    };
  }
}
