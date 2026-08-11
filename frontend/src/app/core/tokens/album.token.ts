import { InjectionToken } from '@angular/core';
import { Observable } from 'rxjs';
import {
  AlbumDetailResponse,
  AlbumIngestRequest,
  AlbumIngestResponse,
  EventCreatePayload,
  EventUpdatePayload,
  MasterArtist,
  MasterEvent,
  MasterFranchise,
  PaginatedAlbumsResponse,
  PaginatedEventsResponse,
} from '../../domain/models/music.model';

export interface AlbumRepositoryPort {
  fetchAlbums(
    query?: string | null,
    limit?: number,
    offset?: number,
  ): Observable<PaginatedAlbumsResponse>;
  getAlbumDetail(albumId: string): Observable<AlbumDetailResponse>;
  ingestAlbum(payload: AlbumIngestRequest): Observable<AlbumIngestResponse>;
  deleteAlbum(albumId: string): Observable<void>;

  searchArtists(query: string): Observable<MasterArtist[]>;
  createArtist(nameOriginal: string, nameTranslated?: string | null): Observable<MasterArtist>;

  fetchEvents(
    query?: string | null,
    statuses?: string[],
    dateFrom?: string | null,
    dateTo?: string | null,
    sortBy?: string,
    sortOrder?: string,
    limit?: number,
    offset?: number,
  ): Observable<PaginatedEventsResponse>;
  searchEvents(query: string, limit?: number): Observable<MasterEvent[]>;
  getEventDetail(eventId: string): Observable<MasterEvent>;
  createEvent(shortName: string): Observable<MasterEvent>;
  createEventFull(payload: EventCreatePayload): Observable<MasterEvent>;
  updateEvent(eventId: string, payload: EventUpdatePayload): Observable<MasterEvent>;
  deleteEvent(eventId: string): Observable<void>;

  searchFranchises(query: string): Observable<MasterFranchise[]>;
  createFranchise(nameOriginal: string): Observable<MasterFranchise>;
  getLabels(query: string): Observable<string[]>;
  getPublishers(query: string): Observable<string[]>;
}

export const ALBUM_REPOSITORY_PORT = new InjectionToken<AlbumRepositoryPort>(
  'Core Music Archival Repository Infrastructure Port Boundary',
);
