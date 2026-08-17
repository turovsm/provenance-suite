import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';
import { ALBUM_REPOSITORY_PORT } from '../../../core/tokens/album.token';
import { AlbumDetailResponse } from '../../../domain/models/music.model';
import { AlbumFormBuilderService } from './album-form-builder.service';

describe('AlbumFormBuilderService', () => {
  let builder: AlbumFormBuilderService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [AlbumFormBuilderService, { provide: ALBUM_REPOSITORY_PORT, useValue: {} }],
    });
    builder = TestBed.inject(AlbumFormBuilderService);
  });

  it('builds a reactive album form group with empty default arrays', () => {
    const form = builder.buildAlbumForm();
    expect(form.get('title_original')).toBeTruthy();
    expect(form.get('original_folder_name')).toBeTruthy();
    expect(builder.discsOf(form).length).toBe(0);
    expect(builder.archivesOf(form).length).toBe(0);
  });

  it('populates form from existing album detail response', () => {
    const form = builder.buildAlbumForm();
    const mockDetail: AlbumDetailResponse = {
      id: 'a1',
      title_original: 'Scarlet Meister',
      aliases: ['SM'],
      release_year: 2024,
      release_month: 8,
      release_day: 15,
      label: 'Sample Label',
      publisher: 'Sample Publisher',
      original_folder_name: 'SM_2024',
      album_artist: { id: 'art1', name_original: 'ZUN', aliases: [] },
      discs: [
        {
          id: 'd1',
          disc_number: 1,
          catalog_number: 'SM-001',
          media_type: 'CD',
          container_format: 'Tracks',
          log_type: 'EAC',
          log_score: 100,
          raw_log_text: null,
          raw_cue_text: null,
          accuraterip_summary: null,
          tracks: [
            {
              id: 't1',
              track_number: 1,
              title_original: 'Track 1',
              aliases: [],
              duration_seconds: 240,
              audio_codec: 'FLAC',
              is_instrumental: false,
              bit_depth: 16,
              sample_rate: 44100,
              artists: [{ id: 'art1', name_original: 'ZUN', aliases: [], role: 'Composer' }],
            },
          ],
        },
      ],
      covers: [],
      archives: [],
      external_links: [{ id: 'el1', site_name: 'VGMdb', url: 'https://vgmdb.net/123' }],
      changelogs: [],
    };

    builder.populateFromAlbum(form, mockDetail);

    expect(form.get('title_original')?.value).toBe('Scarlet Meister');
    expect(form.get('release_date_str')?.value).toBe('2024/08/15');
    expect(builder.discsOf(form).length).toBe(1);
    expect(builder.discsOf(form).at(0).get('catalog_number')?.value).toBe('SM-001');
    expect(builder.externalLinksOf(form).length).toBe(1);
  });

  it('resets form to default single-disc state', () => {
    const form = builder.buildAlbumForm();
    builder.populateDiscsFromSeeds(builder.discsOf(form), [{ disc_number: 1 }, { disc_number: 2 }]);
    expect(builder.discsOf(form).length).toBe(2);

    builder.resetToDefaults(form);

    expect(builder.discsOf(form).length).toBe(1);
    expect(form.get('title_original')?.value).toBeNull();
  });
});
