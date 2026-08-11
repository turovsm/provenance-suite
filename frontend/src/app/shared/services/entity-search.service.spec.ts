import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { EntitySearchService } from './entity-search.service';
import { ALBUM_REPOSITORY_PORT, AlbumRepositoryPort } from '../../core/tokens/album.token';

describe('EntitySearchService', () => {
  let service: EntitySearchService;
  let repoSpy: Record<keyof AlbumRepositoryPort, ReturnType<typeof vi.fn>>;

  beforeEach(() => {
    repoSpy = {
      fetchAlbums: vi.fn(),
      getAlbumDetail: vi.fn(),
      ingestAlbum: vi.fn(),
      deleteAlbum: vi.fn(),
      searchArtists: vi.fn(),
      fetchEvents: vi.fn(),
      searchEvents: vi.fn(),
      getEventDetail: vi.fn(),
      createEvent: vi.fn(),
      createEventFull: vi.fn(),
      updateEvent: vi.fn(),
      deleteEvent: vi.fn(),
      searchFranchises: vi.fn(),
      getLabels: vi.fn(),
      getPublishers: vi.fn(),
      createArtist: vi.fn(),
      createFranchise: vi.fn(),
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

  it('resolves master entity by ID via search matching', () => {
    repoSpy.searchArtists.mockReturnValue(
      of([{ id: 'target-uuid', name_original: 'ZUN', aliases: [] }]),
    );

    service.resolveById('artist', 'target-uuid').subscribe((match) => {
      expect(match).not.toBeNull();
      expect(match?.display).toBe('ZUN');
    });
  });

  it('returns null for free-text entity creation without a backend record', () => {
    service.create('label', 'Independent').subscribe((res) => {
      expect(res).toBeNull();
    });
    expect(repoSpy.createArtist).not.toHaveBeenCalled();
  });
});
