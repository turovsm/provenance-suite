import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { ALBUM_REPOSITORY_PORT, AlbumRepositoryPort } from '../../core/tokens/album.token';
import { EntitySearchService } from './entity-search.service';

describe('EntitySearchService', () => {
  let service: EntitySearchService;
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
      providers: [EntitySearchService, { provide: ALBUM_REPOSITORY_PORT, useValue: repoSpy }],
    });

    service = TestBed.inject(EntitySearchService);
  });

  it('normalizes artist search results into AutocompleteOption array', () => {
    repoSpy.searchArtists.mockReturnValue(
      of([{ id: 'a1', name_original: '上海アリス幻樂団', aliases: ['Team Shanghai Alice'] }]),
    );

    service.search('artist', 'Shanghai').subscribe((options) => {
      expect(options.length).toBe(1);
      expect(options[0].id).toBe('a1');
      expect(options[0].display).toBe('上海アリス幻樂団');
      expect(options[0].subValue).toBe('Team Shanghai Alice');
    });

    expect(repoSpy.searchArtists).toHaveBeenCalledWith('Shanghai');
  });

  it('resolves master entity by ID via detail lookup', () => {
    repoSpy.getArtistDetail.mockReturnValue(
      of({ id: 'target-uuid', name_original: 'ZUN', aliases: [] }),
    );

    service.resolveById('artist', 'target-uuid').subscribe((match) => {
      expect(match).not.toBeNull();
      expect(match?.display).toBe('ZUN');
    });
  });

  it('returns autocomplete option for free-text label/publisher entity creation', () => {
    repoSpy.createLabel.mockReturnValue(
      of({ id: 'label:Independent', name_original: 'Independent', aliases: [] }),
    );

    service.create('label', 'Independent').subscribe((res) => {
      expect(res).not.toBeNull();
      expect(res?.display).toBe('Independent');
    });
    expect(repoSpy.createLabel).toHaveBeenCalledWith({ name_original: 'Independent' });
  });
});
