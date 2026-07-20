import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { LibraryCategory, PaginatedAlbumsResponse } from '../../domain/models/music.model';
import { AlbumRepositoryPort } from '../tokens/album.token';

@Injectable({
  providedIn: 'root',
})
export class HttpAlbumAdapter implements AlbumRepositoryPort {
  private readonly http = inject(HttpClient);
  private readonly endpoint = 'http://localhost:8000/api/v1/albums';

  fetchAlbums(
    category?: LibraryCategory | null,
    query?: string | null,
    limit = 50,
    offset = 0,
  ): Observable<PaginatedAlbumsResponse> {
    let params = new HttpParams().set('limit', limit.toString()).set('offset', offset.toString());

    if (category) {
      params = params.set('category', category);
    }
    if (query && query.trim()) {
      params = params.set('query', query.trim());
    }

    return this.http.get<PaginatedAlbumsResponse>(this.endpoint, { params });
  }

  deleteAlbum(albumId: string): Observable<void> {
    return this.http.delete<void>(`${this.endpoint}/${albumId}`);
  }
}
