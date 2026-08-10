import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
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
} from '../../domain/models/music.model';
import { AlbumRepositoryPort } from '../tokens/album.token';

@Injectable({
  providedIn: 'root',
})
export class HttpAlbumAdapter implements AlbumRepositoryPort {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  fetchAlbums(query?: string | null, limit = 50, offset = 0): Observable<PaginatedAlbumsResponse> {
    let params = new HttpParams().set('limit', limit.toString()).set('offset', offset.toString());
    if (query && query.trim()) params = params.set('query', query.trim());
    return this.http.get<PaginatedAlbumsResponse>(`${this.baseUrl}/albums`, { params });
  }

  getAlbumDetail(albumId: string): Observable<AlbumDetailResponse> {
    return this.http.get<AlbumDetailResponse>(`${this.baseUrl}/albums/${albumId}`);
  }

  ingestAlbum(payload: AlbumIngestRequest): Observable<AlbumIngestResponse> {
    return this.http.post<AlbumIngestResponse>(`${this.baseUrl}/albums`, payload);
  }

  deleteAlbum(albumId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/albums/${albumId}`);
  }

  searchArtists(query: string): Observable<MasterArtist[]> {
    const params = new HttpParams().set('query', query);
    return this.http.get<MasterArtist[]>(`${this.baseUrl}/entities/artists`, { params });
  }

  createArtist(nameOriginal: string, nameTranslated?: string | null): Observable<MasterArtist> {
    return this.http.post<MasterArtist>(`${this.baseUrl}/entities/artists`, {
      name_original: nameOriginal,
      name_translated: nameTranslated ?? null,
    });
  }

  searchEvents(query: string, limit = 20): Observable<MasterEvent[]> {
    const params = new HttpParams().set('query', query).set('limit', limit.toString());
    return this.http.get<MasterEvent[]>(`${this.baseUrl}/entities/events`, { params });
  }

  getEventDetail(eventId: string): Observable<MasterEvent> {
    return this.http.get<MasterEvent>(`${this.baseUrl}/entities/events/${eventId}`);
  }

  createEvent(shortName: string): Observable<MasterEvent> {
    return this.http.post<MasterEvent>(`${this.baseUrl}/entities/events`, {
      short_name: shortName,
    });
  }

  createEventFull(payload: EventCreatePayload): Observable<MasterEvent> {
    return this.http.post<MasterEvent>(`${this.baseUrl}/entities/events`, payload);
  }

  updateEvent(eventId: string, payload: EventUpdatePayload): Observable<MasterEvent> {
    return this.http.put<MasterEvent>(`${this.baseUrl}/entities/events/${eventId}`, payload);
  }

  deleteEvent(eventId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/entities/events/${eventId}`);
  }

  searchFranchises(query: string): Observable<MasterFranchise[]> {
    const params = new HttpParams().set('query', query);
    return this.http.get<MasterFranchise[]>(`${this.baseUrl}/entities/franchises`, { params });
  }

  createFranchise(nameOriginal: string): Observable<MasterFranchise> {
    return this.http.post<MasterFranchise>(`${this.baseUrl}/entities/franchises`, {
      name_original: nameOriginal,
    });
  }

  getLabels(query: string): Observable<string[]> {
    const params = new HttpParams().set('query', query);
    return this.http.get<string[]>(`${this.baseUrl}/entities/labels`, { params });
  }

  getPublishers(query: string): Observable<string[]> {
    const params = new HttpParams().set('query', query);
    return this.http.get<string[]>(`${this.baseUrl}/entities/publishers`, { params });
  }
}
