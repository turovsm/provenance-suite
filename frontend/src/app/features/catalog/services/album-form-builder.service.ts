import { Injectable, inject } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AlbumDetailResponse, MasterArtist } from '../../../domain/models/music.model';
import { EntitySearchService } from '../../../shared/services/entity-search.service';
import { fuzzyDateValidator } from '../../../shared/validators/fuzzy-date.validator';
import {
  AlbumFormRawValue,
  ArchiveLinkSeed,
  ArchiveSeed,
  ArtistSeed,
  DiscSeed,
  ExternalLinkSeed,
  TrackSeed,
} from '../models/album-form.model';

@Injectable({ providedIn: 'root' })
export class AlbumFormBuilderService {
  private readonly fb = inject(FormBuilder);
  private readonly entitySearch = inject(EntitySearchService);

  buildAlbumForm(): FormGroup {
    return this.fb.group({
      album_id: [null],
      title_original: ['', [Validators.required, Validators.maxLength(512)]],
      aliases: [[]],
      original_folder_name: ['', [Validators.required, Validators.maxLength(1024)]],
      release_date_str: ['', [fuzzyDateValidator()]],
      label: [''],
      publisher: [''],
      storage_drive: ['', [Validators.maxLength(64)]],
      relative_path: ['', [Validators.maxLength(1024)]],
      event_id: [null],
      franchise_id: [null],
      album_artist_id: [null],
      discs: this.fb.array([]),
      archives: this.fb.array([]),
      external_links: this.fb.array([]),
    });
  }

  createArtistGroup(data?: ArtistSeed): FormGroup {
    return this.fb.group({
      name_original: [data?.name_original || '', [Validators.required, Validators.maxLength(512)]],
      role: [data?.role || 'Composer', Validators.required],
    });
  }

  createTrackGroup(t?: TrackSeed): FormGroup {
    const trackGroup = this.fb.group({
      track_number: [t?.track_number ?? 1, [Validators.required, Validators.min(1)]],
      title_original: [t?.title_original || '', Validators.required],
      aliases: [t?.aliases ?? []],
      duration_seconds: [t?.duration_seconds ?? null, Validators.min(0)],
      audio_codec: [t?.audio_codec || 'FLAC'],
      video_codec: [t?.video_codec || ''],
      bit_depth: [t?.bit_depth ?? null, Validators.min(0)],
      sample_rate: [t?.sample_rate ?? null, Validators.min(0)],
      bitrate_kbps: [t?.bitrate_kbps ?? null, Validators.min(0)],
      bitrate_mode: [t?.bitrate_mode || ''],
      is_instrumental: [Boolean(t?.is_instrumental)],
      artists: this.fb.array([]),
    });

    const artists = trackGroup.get('artists') as FormArray;
    if (Array.isArray(t?.artists)) {
      t.artists.forEach((ta) =>
        artists.push(this.createArtistGroup({ ...ta, role: ta.role || 'Composer' })),
      );
    }
    return trackGroup;
  }

  createDiscGroup(d?: DiscSeed): FormGroup {
    const discGroup = this.fb.group({
      disc_number: [d?.disc_number ?? 1, [Validators.required, Validators.min(1)]],
      media_type: [d?.media_type || 'CD', Validators.required],
      container_format: [d?.container_format || 'Tracks', Validators.required],
      catalog_number: [d?.catalog_number || ''],
      log_type: [d?.log_type || ''],
      log_score: [d?.log_score ?? null, [Validators.max(100)]],
      raw_log_text: [d?.raw_log_text || ''],
      raw_cue_text: [d?.raw_cue_text || ''],
      accuraterip_summary: [d?.accuraterip_summary || ''],
      tracks: this.fb.array([]),
    });

    const tracks = discGroup.get('tracks') as FormArray;
    if (Array.isArray(d?.tracks) && d.tracks.length > 0) {
      d.tracks.forEach((t) => tracks.push(this.createTrackGroup(t)));
    } else {
      tracks.push(this.createTrackGroup({ track_number: 1 }));
    }
    return discGroup;
  }

  populateDiscsFromSeeds(discsArray: FormArray, seeds: DiscSeed[]): void {
    discsArray.clear();
    if (Array.isArray(seeds) && seeds.length > 0) {
      seeds.forEach((d) => discsArray.push(this.createDiscGroup(d)));
    } else {
      discsArray.push(this.createDiscGroup({ disc_number: 1 }));
    }
  }

  createArchiveLinkGroup(lnk?: ArchiveLinkSeed): FormGroup {
    return this.fb.group({
      provider_name: [lnk?.provider_name || 'Mega', Validators.required],
      download_url: [lnk?.download_url || '', Validators.required],
      is_active: [lnk?.is_active ?? true],
    });
  }

  createArchiveGroup(a?: ArchiveSeed): FormGroup {
    const archGroup = this.fb.group({
      archive_name: [a?.archive_name || '', Validators.required],
      encryption_password: [a?.encryption_password || ''],
      file_size_bytes: [a?.file_size_bytes ?? null, Validators.min(0)],
      hash_sha256: [a?.hash_sha256 || '', Validators.maxLength(64)],
      links: this.fb.array([]),
    });

    const links = archGroup.get('links') as FormArray;
    if (Array.isArray(a?.links) && a.links.length > 0) {
      a.links.forEach((lnk) => links.push(this.createArchiveLinkGroup(lnk)));
    } else {
      links.push(this.createArchiveLinkGroup());
    }
    return archGroup;
  }

  createExternalLinkGroup(el?: ExternalLinkSeed): FormGroup {
    return this.fb.group({
      site_name: [el?.site_name || 'VGMdb', Validators.required],
      url: [el?.url || '', Validators.required],
    });
  }

  resetToDefaults(form: FormGroup): void {
    form.reset();
    this.clearArrays(form);
    this.discsOf(form).push(this.createDiscGroup({ disc_number: 1 }));
  }

  populateFromAlbum(form: FormGroup, album: AlbumDetailResponse): void {
    this.clearArrays(form);

    let releaseDateStr = '';
    if (album.release_year) {
      const y = album.release_year.toString();
      const m = album.release_month ? album.release_month.toString().padStart(2, '0') : 'XX';
      const d = album.release_day ? album.release_day.toString().padStart(2, '0') : 'XX';
      if (m === 'XX' && d === 'XX') {
        releaseDateStr = `${y}/XX/XX`;
      } else if (d === 'XX') {
        releaseDateStr = `${y}/${m}/XX`;
      } else {
        releaseDateStr = `${y}/${m}/${d}`;
      }
    }

    if (album.album_artist) {
      this.entitySearch.cacheOption('artist', {
        id: album.album_artist.id,
        display: album.album_artist.name_original,
        raw: album.album_artist as MasterArtist,
      });
    }

    if (album.label) {
      const labelDisplay =
        typeof album.label === 'string' ? album.label : album.label.name_original;
      const labelId = typeof album.label === 'string' ? `label:${album.label}` : album.label.id;
      this.entitySearch.cacheOption('label', {
        id: labelId,
        display: labelDisplay,
        raw: album.label,
      });
    }

    if (album.publisher) {
      const publisherDisplay =
        typeof album.publisher === 'string' ? album.publisher : album.publisher.name_original;
      const publisherId =
        typeof album.publisher === 'string' ? `publisher:${album.publisher}` : album.publisher.id;
      this.entitySearch.cacheOption('publisher', {
        id: publisherId,
        display: publisherDisplay,
        raw: album.publisher,
      });
    }

    const labelFormVal =
      typeof album.label === 'string' ? album.label : album.label?.name_original || '';
    const publisherFormVal =
      typeof album.publisher === 'string' ? album.publisher : album.publisher?.name_original || '';

    form.patchValue({
      album_id: album.id,
      title_original: album.title_original,
      aliases: album.aliases ?? [],
      original_folder_name: album.original_folder_name,
      release_date_str: releaseDateStr,
      label: labelFormVal,
      publisher: publisherFormVal,
      storage_drive: album.storage_drive || '',
      relative_path: album.relative_path || '',
      event_id: album.event_id || null,
      franchise_id: album.franchise_id || null,
      album_artist_id: album.album_artist?.id || album.album_artist?.name_original || null,
    });

    (album.discs ?? []).forEach((d) => this.discsOf(form).push(this.createDiscGroup(d)));
    if (this.discsOf(form).length === 0) {
      this.discsOf(form).push(this.createDiscGroup({ disc_number: 1 }));
    }
    (album.archives ?? []).forEach((a) => this.archivesOf(form).push(this.createArchiveGroup(a)));
    (album.external_links ?? []).forEach((el) =>
      this.externalLinksOf(form).push(this.createExternalLinkGroup(el)),
    );
  }

  applyDraftFormValue(form: FormGroup, fVal: AlbumFormRawValue): void {
    this.clearArrays(form);

    let draftDateStr = fVal.release_date_str || '';
    if (!draftDateStr && fVal.release_year) {
      const y = fVal.release_year.toString();
      const m = fVal.release_month ? fVal.release_month.toString().padStart(2, '0') : 'XX';
      const d = fVal.release_day ? fVal.release_day.toString().padStart(2, '0') : 'XX';
      draftDateStr = `${y}/${m}/${d}`;
    }

    form.patchValue({
      title_original: fVal.title_original || '',
      aliases: fVal.aliases ?? [],
      original_folder_name: fVal.original_folder_name || '',
      release_date_str: draftDateStr,
      label: fVal.label || '',
      publisher: fVal.publisher || '',
      storage_drive: fVal.storage_drive || '',
      relative_path: fVal.relative_path || '',
      event_id: fVal.event_id || null,
      franchise_id: fVal.franchise_id || null,
      album_artist_id: fVal.album_artist_id || null,
    });

    if (Array.isArray(fVal.discs) && fVal.discs.length > 0) {
      fVal.discs.forEach((d) => this.discsOf(form).push(this.createDiscGroup(d)));
    } else {
      this.discsOf(form).push(this.createDiscGroup({ disc_number: 1 }));
    }
    if (Array.isArray(fVal.archives)) {
      fVal.archives.forEach((a) => this.archivesOf(form).push(this.createArchiveGroup(a)));
    }
    if (Array.isArray(fVal.external_links)) {
      fVal.external_links.forEach((el) =>
        this.externalLinksOf(form).push(this.createExternalLinkGroup(el)),
      );
    }
  }

  clearArrays(form: FormGroup): void {
    this.discsOf(form).clear();
    this.archivesOf(form).clear();
    this.externalLinksOf(form).clear();
  }

  discsOf(form: FormGroup): FormArray {
    return form.get('discs') as FormArray;
  }

  archivesOf(form: FormGroup): FormArray {
    return form.get('archives') as FormArray;
  }

  externalLinksOf(form: FormGroup): FormArray {
    return form.get('external_links') as FormArray;
  }
}
