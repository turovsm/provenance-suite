import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ALBUM_REPOSITORY_PORT, AlbumRepositoryPort } from '../../../core/tokens/album.token';
import { ArtistDiscography, MasterArtist } from '../../../domain/models/music.model';
import { EntityStateEngine } from './entity.state';

describe('EntityStateEngine', () => {
  let state: EntityStateEngine;
  let repoSpy: Record<keyof AlbumRepositoryPort, ReturnType<typeof vi.fn>>;

  const mockArtist: MasterArtist = {
    id: 'a1',
    name_original: 'ZUN',
    aliases: ['Team Shanghai Alice'],
    image_url: 'http://cdn/zun.jpg',
    description: 'Creator of Touhou Project',
    created_at: '2026-01-01',
  };

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
      providers: [EntityStateEngine, { provide: ALBUM_REPOSITORY_PORT, useValue: repoSpy }],
    });

    state = TestBed.inject(EntityStateEngine);
  });

  it('queries master entity directory and updates signals', () => {
    repoSpy.fetchEntities.mockReturnValue(
      of({
        items: [{ id: 'a1', name_original: 'ZUN', aliases: [], entity_type: 'artist' }],
        total_count: 1,
        limit: 24,
        offset: 0,
      }),
    );

    state.queryDirectory();

    expect(state.isLoading()).toBe(false);
    expect(state.hasEntities()).toBe(true);
    expect(state.entities().length).toBe(1);
    expect(state.totalCount()).toBe(1);
  });

  it('switches entity category type and resets page', () => {
    repoSpy.fetchEntities.mockReturnValue(of({ items: [], total_count: 0, limit: 24, offset: 0 }));

    state.setPage(3);
    state.setActiveType('franchise');

    expect(state.activeType()).toBe('franchise');
    expect(state.currentPage()).toBe(1);
    expect(repoSpy.fetchEntities).toHaveBeenCalledWith('franchise', '', 24, 0);
  });

  it('loads artist detail and fetches associated discography', () => {
    const mockDisco: ArtistDiscography = {
      artist_id: 'a1',
      main_albums: [],
      contribution_albums: [],
    };
    repoSpy.getArtistDetail.mockReturnValue(of(mockArtist));
    repoSpy.getArtistDiscography.mockReturnValue(of(mockDisco));

    state.loadEntityDetail('artist', 'a1');

    expect(state.activeArtistDetail()).toEqual(mockArtist);
    expect(state.artistDiscography()).toEqual(mockDisco);
  });

  it('executes artist creation and triggers directory reload', () => {
    repoSpy.createArtistFull.mockReturnValue(of(mockArtist));
    repoSpy.fetchEntities.mockReturnValue(of({ items: [], total_count: 0, limit: 24, offset: 0 }));
    const onSuccess = vi.fn();

    state.createArtist({ name_original: 'ZUN', aliases: [] }, onSuccess);

    expect(repoSpy.createArtistFull).toHaveBeenCalledWith({ name_original: 'ZUN', aliases: [] });
    expect(onSuccess).toHaveBeenCalled();
  });
});
