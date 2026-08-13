import { TestBed } from '@angular/core/testing';
import { AlbumPayloadMapperService } from './album-payload-mapper.service';
import { AlbumFormRawValue, LocalCoverItem } from '../models/album-form.model';

describe('AlbumPayloadMapperService', () => {
  let service: AlbumPayloadMapperService;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [AlbumPayloadMapperService] });
    service = TestBed.inject(AlbumPayloadMapperService);
  });

  it('transforms raw reactive form value and cover list into clean API ingest request', () => {
    const rawForm: AlbumFormRawValue = {
      title_original: 'Test Original',
      original_folder_name: 'Folder_01',
      release_date_str: '2024/08/15',
      album_artist_id: 'a8123456-1234-1234-1234-123456789abc',
      event_id: 'b8123456-1234-1234-1234-123456789abc',
      franchise_id: 'c8123456-1234-1234-1234-123456789abc',
      discs: [
        {
          disc_number: '1',
          media_type: 'CD',
          container_format: 'Tracks',
          tracks: [
            {
              track_number: 1,
              title_original: 'Track 1',
              duration_seconds: '240',
              is_instrumental: true,
              artists: [{ name_original: 'ZUN', role: 'Composer' }],
            },
          ],
        },
      ],
    };

    const mockCovers: LocalCoverItem[] = [
      {
        id: 'c1',
        base64:
          'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        mimeType: 'image/jpeg',
        fileName: 'cover.jpg',
        fileSize: 1024,
        coverType: 'Front',
        previewUrl: 'blob:http://localhost/1234',
      },
    ];

    const result = service.toIngestRequest(rawForm, mockCovers);

    expect(result.title_original).toBe('Test Original');
    expect(result.release_year).toBe(2024);
    expect(result.release_month).toBe(8);
    expect(result.release_day).toBe(15);
    expect(result.album_artist_id).toBe('a8123456-1234-1234-1234-123456789abc');
    expect(result.event_id).toBe('b8123456-1234-1234-1234-123456789abc');
    expect(result.franchise_id).toBe('c8123456-1234-1234-1234-123456789abc');
    expect(result.album_artist).toBeNull();
    expect(result.discs[0].tracks[0].duration_seconds).toBe(240);
    expect(result.discs[0].tracks[0].is_instrumental).toBe(true);
    expect(result.covers.length).toBe(1);
    expect(result.covers[0].cover_type).toBe('Front');
  });

  it('maps plain artist/event/franchise strings to null IDs while preserving names', () => {
    const rawForm: AlbumFormRawValue = {
      title_original: 'Independent Release',
      original_folder_name: 'Indie_01',
      album_artist_id: 'Custom Circle Name',
      event_id: 'Comiket 70',
      franchise_id: 'ぶらばん！',
    };

    const result = service.toIngestRequest(rawForm, []);

    expect(result.album_artist_id).toBeNull();
    expect(result.event_id).toBeNull();
    expect(result.franchise_id).toBeNull();
    expect(result.album_artist?.name_original).toBe('Custom Circle Name');
  });
});
