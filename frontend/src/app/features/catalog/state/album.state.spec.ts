import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { ALBUM_REPOSITORY_PORT, AlbumRepositoryPort } from '../../../core/tokens/album.token';
import { AlbumSummary } from '../../../domain/models/music.model';
import { AlbumStateEngine } from './album.state';

describe('AlbumStateEngine', () => {
  let state: AlbumStateEngine;
  let repoSpy: Record<keyof AlbumRepositoryPort, ReturnType<typeof vi.fn>>;

  beforeEach(() => {
    repoSpy = {
      fetchAlbums: vi.fn(),
      getAlbumDetail: vi.fn(),
      ingestAlbum: vi.fn(),
      deleteAlbum: vi.fn(),
      fetchEntities: vi.fn(),
      searchArtists: vi.fn(),
      getArtistDetail: vi.fn(),
      getArtistDiscography: vi.fn(),
      createArtist: vi.fn(),
      createArtistFull: vi.fn(),
      updateArtist: vi.fn(),
      deleteArtist: vi.fn(),
      searchFranchises: vi.fn(),
      getFranchiseDetail: vi.fn(),
      getFranchiseAlbums: vi.fn(),
      createFranchise: vi.fn(),
      createFranchiseFull: vi.fn(),
      updateFranchise: vi.fn(),
      deleteFranchise: vi.fn(),
      searchLabels: vi.fn(),
      getLabelDetail: vi.fn(),
      getLabelAlbums: vi.fn(),
      createLabel: vi.fn(),
      updateLabel: vi.fn(),
      deleteLabel: vi.fn(),
      searchPublishers: vi.fn(),
      getPublisherDetail: vi.fn(),
      getPublisherAlbums: vi.fn(),
      createPublisher: vi.fn(),
      updatePublisher: vi.fn(),
      deletePublisher: vi.fn(),
      fetchEvents: vi.fn(),
      searchEvents: vi.fn(),
      getEventDetail: vi.fn(),
      createEvent: vi.fn(),
      createEventFull: vi.fn(),
      updateEvent: vi.fn(),
      deleteEvent: vi.fn(),
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
