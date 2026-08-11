import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
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
  PaginatedEventsResponse,
} from '../../domain/models/music.model';
import { AlbumRepositoryPort } from '../tokens/album.token';

function normalizeFilterDate(d: string | null | undefined, isEndBound = false): string | null {
  if (!d || !d.trim()) return null;
  const cleaned = d.trim().replace(/[./]/g, '-').toLowerCase();
  const parts = cleaned.split('-');

  if (parts.length === 3) {
    const yNum = parseInt(parts[0], 10);
    let mStr = parts[1];
    let dayStr = parts[2];

    if (mStr === 'xx') {
      mStr = isEndBound ? '12' : '01';
    }
    if (dayStr === 'xx') {
      dayStr = isEndBound ? '31' : '01';
    }

    const mNum = parseInt(mStr, 10);
    const dNum = parseInt(dayStr, 10);

    if (!isNaN(yNum) && !isNaN(mNum) && !isNaN(dNum)) {
      return `${yNum}-${String(mNum).padStart(2, '0')}-${String(dNum).padStart(2, '0')}`;
    }
  }

  return cleaned;
}

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

  fetchEvents(
    query?: string | null,
    statuses?: string[],
    dateFrom?: string | null,
    dateTo?: string | null,
    sortBy = 'start_date',
    sortOrder = 'desc',
    limit = 50,
    offset = 0,
  ): Observable<PaginatedEventsResponse> {
    let params = new HttpParams()
      .set('sort_by', sortBy)
      .set('sort_order', sortOrder)
      .set('limit', limit.toString())
      .set('offset', offset.toString());

    if (query && query.trim()) params = params.set('query', query.trim());
    if (statuses && statuses.length > 0) {
      statuses.forEach((s) => {
        params = params.append('status', s);
      });
    }

    const normFrom = normalizeFilterDate(dateFrom, false);
    if (normFrom) params = params.set('date_from', normFrom);

    const normTo = normalizeFilterDate(dateTo, true);
    if (normTo) params = params.set('date_to', normTo);

    return this.http.get<PaginatedEventsResponse>(`${this.baseUrl}/entities/events`, { params });
  }

  searchEvents(query: string, limit = 20): Observable<MasterEvent[]> {
    return this.fetchEvents(query, undefined, null, null, 'short_name', 'asc', limit, 0).pipe(
      map((res) => res.items),
    );
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
