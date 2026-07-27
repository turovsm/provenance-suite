import { InjectionToken } from '@angular/core';
import { Observable } from 'rxjs';
import {
  AlbumDetailResponse,
  AlbumIngestRequest,
  AlbumIngestResponse,
  MasterArtist,
  MasterEvent,
  MasterFranchise,
  PaginatedAlbumsResponse,
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
  searchEvents(query: string): Observable<MasterEvent[]>;
  createEvent(shortName: string): Observable<MasterEvent>;
  searchFranchises(query: string): Observable<MasterFranchise[]>;
  createFranchise(nameOriginal: string): Observable<MasterFranchise>;
  getLabels(query: string): Observable<string[]>;
  getPublishers(query: string): Observable<string[]>;
}

export const ALBUM_REPOSITORY_PORT = new InjectionToken<AlbumRepositoryPort>(
  'Core Music Archival Repository Infrastructure Port Boundary',
);
