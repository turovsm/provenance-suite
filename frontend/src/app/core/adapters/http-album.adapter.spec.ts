import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { HttpAlbumAdapter } from './http-album.adapter';
import { AlbumIngestRequest } from '../../domain/models/music.model';

describe('HttpAlbumAdapter', () => {
  let adapter: HttpAlbumAdapter;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), HttpAlbumAdapter],
    });

    adapter = TestBed.inject(HttpAlbumAdapter);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('fetches paginated albums with search query parameters', () => {
    adapter.fetchAlbums('Touhou', 20, 40).subscribe((res) => {
      expect(res.total_count).toBe(1);
    });

    const req = httpMock.expectOne(
      (r) =>
        r.url.endsWith('/albums') &&
        r.params.get('query') === 'Touhou' &&
        r.params.get('limit') === '20' &&
        r.params.get('offset') === '40',
    );
    expect(req.request.method).toBe('GET');
    req.flush({ items: [], total_count: 1, limit: 20, offset: 40 });
  });

  it('submits album ingest payload via HTTP POST', () => {
    const mockPayload: AlbumIngestRequest = {
      title_original: 'Symphonic East',
      original_folder_name: 'SE_2024',
      discs: [],
      covers: [],
      archives: [],
      external_links: [],
    };

    adapter.ingestAlbum(mockPayload).subscribe((res) => {
      expect(res.album_id).toBe('generated-uuid');
    });

    const req = httpMock.expectOne((r) => r.url.endsWith('/albums'));
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(mockPayload);
    req.flush({
      album_id: 'generated-uuid',
      title_original: 'Symphonic East',
      total_discs: 0,
      total_tracks: 0,
    });
  });

  it('queries master artist search endpoint', () => {
    adapter.searchArtists('ZUN').subscribe((artists) => {
      expect(artists.length).toBe(1);
      expect(artists[0].name_original).toBe('ZUN');
    });

    const req = httpMock.expectOne(
      (r) => r.url.endsWith('/entities/artists') && r.params.get('query') === 'ZUN',
    );
    expect(req.request.method).toBe('GET');
    req.flush([{ id: 'a1', name_original: 'ZUN', name_translated: 'ZUN' }]);
  });
});
