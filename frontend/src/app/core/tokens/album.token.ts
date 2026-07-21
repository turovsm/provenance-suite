import { InjectionToken } from '@angular/core';
import { Observable } from 'rxjs';
import {
  AlbumIngestRequest,
  AlbumIngestResponse,
  LibraryCategory,
  PaginatedAlbumsResponse,
} from '../../domain/models/music.model';

export interface AlbumRepositoryPort {
  fetchAlbums(
    category?: LibraryCategory | null,
    query?: string | null,
    limit?: number,
    offset?: number,
  ): Observable<PaginatedAlbumsResponse>;
  ingestAlbum(payload: AlbumIngestRequest): Observable<AlbumIngestResponse>;
  deleteAlbum(albumId: string): Observable<void>;
}

export const ALBUM_REPOSITORY_PORT = new InjectionToken<AlbumRepositoryPort>(
  'Core Music Archival Repository Infrastructure Port Boundary',
);
