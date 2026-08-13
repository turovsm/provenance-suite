import { InjectionToken } from '@angular/core';
import { Observable } from 'rxjs';
import {
  AlbumDetailResponse,
  AlbumIngestRequest,
  AlbumIngestResponse,
  AlbumSummary,
  ArtistCreatePayload,
  ArtistDiscography,
  ArtistUpdatePayload,
  EventCreatePayload,
  EventUpdatePayload,
  FranchiseCreatePayload,
  FranchiseUpdatePayload,
  LabelCreatePayload,
  LabelUpdatePayload,
  MasterArtist,
  MasterEvent,
  MasterFranchise,
  MasterLabel,
  MasterPublisher,
  PaginatedAlbumsResponse,
  PaginatedEntitiesResponse,
  PaginatedEventsResponse,
  PublisherCreatePayload,
  PublisherUpdatePayload,
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

  fetchEntities(
    type?: string,
    query?: string | null,
    limit?: number,
    offset?: number,
  ): Observable<PaginatedEntitiesResponse>;

  searchArtists(query: string, limit?: number): Observable<MasterArtist[]>;
  getArtistDetail(artistId: string): Observable<MasterArtist>;
  getArtistDiscography(artistId: string): Observable<ArtistDiscography>;
  createArtist(nameOriginal: string, nameTranslated?: string | null): Observable<MasterArtist>;
  createArtistFull(payload: ArtistCreatePayload): Observable<MasterArtist>;
  updateArtist(artistId: string, payload: ArtistUpdatePayload): Observable<MasterArtist>;
  deleteArtist(artistId: string): Observable<void>;

  searchFranchises(query: string, limit?: number): Observable<MasterFranchise[]>;
  getFranchiseDetail(franchiseId: string): Observable<MasterFranchise>;
  getFranchiseAlbums(franchiseId: string): Observable<AlbumSummary[]>;
  createFranchise(nameOriginal: string): Observable<MasterFranchise>;
  createFranchiseFull(payload: FranchiseCreatePayload): Observable<MasterFranchise>;
  updateFranchise(
    franchiseId: string,
    payload: FranchiseUpdatePayload,
  ): Observable<MasterFranchise>;
  deleteFranchise(franchiseId: string): Observable<void>;

  searchLabels(query: string, limit?: number): Observable<MasterLabel[]>;
  getLabelDetail(labelId: string): Observable<MasterLabel>;
  getLabelAlbums(labelId: string): Observable<AlbumSummary[]>;
  createLabel(payload: LabelCreatePayload): Observable<MasterLabel>;
  updateLabel(labelId: string, payload: LabelUpdatePayload): Observable<MasterLabel>;
  deleteLabel(labelId: string): Observable<void>;

  searchPublishers(query: string, limit?: number): Observable<MasterPublisher[]>;
  getPublisherDetail(publisherId: string): Observable<MasterPublisher>;
  getPublisherAlbums(publisherId: string): Observable<AlbumSummary[]>;
  createPublisher(payload: PublisherCreatePayload): Observable<MasterPublisher>;
  updatePublisher(
    publisherId: string,
    payload: PublisherUpdatePayload,
  ): Observable<MasterPublisher>;
  deletePublisher(publisherId: string): Observable<void>;

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

  getLabels(query: string): Observable<string[]>;
  getPublishers(query: string): Observable<string[]>;
}

export const ALBUM_REPOSITORY_PORT = new InjectionToken<AlbumRepositoryPort>(
  'Core Music Archival Repository Infrastructure Port Boundary',
);
