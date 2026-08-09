import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { AlbumStateEngine } from './album.state';
import { ALBUM_REPOSITORY_PORT, AlbumRepositoryPort } from '../../../core/tokens/album.token';
import { AlbumSummary } from '../../../domain/models/music.model';

describe('AlbumStateEngine', () => {
  let state: AlbumStateEngine;
  let repoSpy: Record<keyof AlbumRepositoryPort, ReturnType<typeof vi.fn>>;

  beforeEach(() => {
    repoSpy = {
      fetchAlbums: vi.fn(),
      getAlbumDetail: vi.fn(),
      ingestAlbum: vi.fn(),
      deleteAlbum: vi.fn(),
      searchArtists: vi.fn(),
      createArtist: vi.fn(),
      searchEvents: vi.fn(),
      createEvent: vi.fn(),
      searchFranchises: vi.fn(),
      createFranchise: vi.fn(),
      getLabels: vi.fn(),
      getPublishers: vi.fn(),
    };

    TestBed.configureTestingModule({
      providers: [AlbumStateEngine, { provide: ALBUM_REPOSITORY_PORT, useValue: repoSpy }],
    });

    state = TestBed.inject(AlbumStateEngine);
  });

  it('queries catalog and updates signal state on success', () => {
    const mockSummary: AlbumSummary = {
      id: 'album-1',
      title_original: 'Album One',
      aliases: [],
      release_year: 2024,
      release_month: null,
      release_day: null,
      label: null,
      publisher: null,
      original_folder_name: 'Album_One',
      album_artist: null,
      total_discs: 1,
      covers: [],
    };

    repoSpy.fetchAlbums.mockReturnValue(
      of({
        items: [mockSummary],
        total_count: 1,
        limit: 24,
        offset: 0,
      }),
    );

    state.queryCatalog();

    expect(state.isLoading()).toBe(false);
    expect(state.hasAlbums()).toBe(true);
    expect(state.albums().length).toBe(1);
    expect(state.totalCount()).toBe(1);
  });

  it('sets error signal when catalog request fails', () => {
    repoSpy.fetchAlbums.mockReturnValue(
      throwError(() => ({ error: { error: { message: 'Database connection offline.' } } })),
    );

    state.queryCatalog();

    expect(state.isLoading()).toBe(false);
    expect(state.error()).toBe('Database connection offline.');
  });

  it('resets active page when setting new search query', () => {
    repoSpy.fetchAlbums.mockReturnValue(of({ items: [], total_count: 0, limit: 24, offset: 0 }));

    state.setPage(3);
    state.setSearchQuery('Touhou');

    expect(state.currentPage()).toBe(1);
    expect(state.searchQuery()).toBe('Touhou');
  });
});
