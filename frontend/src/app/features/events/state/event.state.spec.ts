import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ALBUM_REPOSITORY_PORT, AlbumRepositoryPort } from '../../../core/tokens/album.token';
import { MasterEvent } from '../../../domain/models/music.model';
import { EventStateEngine } from './event.state';

describe('EventStateEngine', () => {
  let state: EventStateEngine;
  let repoSpy: Record<keyof AlbumRepositoryPort, ReturnType<typeof vi.fn>>;

  const mockEvent: MasterEvent = {
    id: 'e1',
    short_name: 'C104',
    full_name: 'Comic Market 104',
    start_date: '2024-08-11',
    end_date: '2024-08-12',
    status: 'HELD',
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
      providers: [EventStateEngine, { provide: ALBUM_REPOSITORY_PORT, useValue: repoSpy }],
    });

    state = TestBed.inject(EventStateEngine);
  });

  it('queries events registry with active filters and pagination', () => {
    repoSpy.fetchEvents.mockReturnValue(
      of({ items: [mockEvent], total_count: 1, limit: 50, offset: 0 }),
    );

    state.queryEvents();

    expect(state.isLoading()).toBe(false);
    expect(state.events().length).toBe(1);
    expect(state.totalCount()).toBe(1);
    expect(state.events()[0].short_name).toBe('C104');
  });

  it('applies date range bounds and triggers reload', () => {
    repoSpy.fetchEvents.mockReturnValue(of({ items: [], total_count: 0, limit: 50, offset: 0 }));

    state.setDateRange('2024-01-01', '2024-12-31');

    expect(state.dateFrom()).toBe('2024-01-01');
    expect(state.dateTo()).toBe('2024-12-31');
    expect(repoSpy.fetchEvents).toHaveBeenCalledWith(
      '',
      expect.any(Array),
      '2024-01-01',
      '2024-12-31',
      'start_date',
      'desc',
      50,
      0,
    );
  });

  it('updates sorting field and order', () => {
    repoSpy.fetchEvents.mockReturnValue(of({ items: [], total_count: 0, limit: 50, offset: 0 }));

    state.setSorting('short_name', 'asc');

    expect(state.sortField()).toBe('short_name');
    expect(state.sortOrder()).toBe('asc');
  });

  it('creates new master event and invokes success callback', () => {
    repoSpy.createEventFull.mockReturnValue(of(mockEvent));
    repoSpy.fetchEvents.mockReturnValue(of({ items: [], total_count: 0, limit: 50, offset: 0 }));
    const onSuccess = vi.fn();

    state.createEvent({ short_name: 'C104', status: 'HELD' }, onSuccess);

    expect(repoSpy.createEventFull).toHaveBeenCalledWith({ short_name: 'C104', status: 'HELD' });
    expect(onSuccess).toHaveBeenCalled();
  });
});
