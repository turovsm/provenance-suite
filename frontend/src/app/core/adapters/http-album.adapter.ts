import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
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

  fetchEntities(
    type = 'all',
    query?: string | null,
    limit = 24,
    offset = 0,
  ): Observable<PaginatedEntitiesResponse> {
    let params = new HttpParams()
      .set('type', type)
      .set('limit', limit.toString())
      .set('offset', offset.toString());
    if (query && query.trim()) params = params.set('query', query.trim());
    return this.http.get<PaginatedEntitiesResponse>(`${this.baseUrl}/entities`, { params });
  }

  searchArtists(query: string, limit = 20): Observable<MasterArtist[]> {
    let params = new HttpParams().set('limit', limit.toString());
    if (query && query.trim()) params = params.set('query', query.trim());
    return this.http.get<MasterArtist[]>(`${this.baseUrl}/entities/artists`, { params });
  }

  getArtistDetail(artistId: string): Observable<MasterArtist> {
    return this.http.get<MasterArtist>(`${this.baseUrl}/entities/artists/${artistId}`);
  }

  getArtistDiscography(artistId: string): Observable<ArtistDiscography> {
    return this.http.get<ArtistDiscography>(
      `${this.baseUrl}/entities/artists/${artistId}/discography`,
    );
  }

  createArtist(nameOriginal: string, nameTranslated?: string | null): Observable<MasterArtist> {
    return this.http.post<MasterArtist>(`${this.baseUrl}/entities/artists`, {
      name_original: nameOriginal,
      aliases: nameTranslated ? [nameTranslated] : [],
    });
  }

  createArtistFull(payload: ArtistCreatePayload): Observable<MasterArtist> {
    return this.http.post<MasterArtist>(`${this.baseUrl}/entities/artists`, payload);
  }

  updateArtist(artistId: string, payload: ArtistUpdatePayload): Observable<MasterArtist> {
    return this.http.put<MasterArtist>(`${this.baseUrl}/entities/artists/${artistId}`, payload);
  }

  deleteArtist(artistId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/entities/artists/${artistId}`);
  }

  searchFranchises(query: string, limit = 20): Observable<MasterFranchise[]> {
    let params = new HttpParams().set('limit', limit.toString());
    if (query && query.trim()) params = params.set('query', query.trim());
    return this.http.get<MasterFranchise[]>(`${this.baseUrl}/entities/franchises`, { params });
  }

  getFranchiseDetail(franchiseId: string): Observable<MasterFranchise> {
    return this.http.get<MasterFranchise>(`${this.baseUrl}/entities/franchises/${franchiseId}`);
  }

  getFranchiseAlbums(franchiseId: string): Observable<AlbumSummary[]> {
    return this.http.get<AlbumSummary[]>(
      `${this.baseUrl}/entities/franchises/${franchiseId}/albums`,
    );
  }

  createFranchise(nameOriginal: string): Observable<MasterFranchise> {
    return this.http.post<MasterFranchise>(`${this.baseUrl}/entities/franchises`, {
      name_original: nameOriginal,
    });
  }

  createFranchiseFull(payload: FranchiseCreatePayload): Observable<MasterFranchise> {
    return this.http.post<MasterFranchise>(`${this.baseUrl}/entities/franchises`, payload);
  }

  updateFranchise(
    franchiseId: string,
    payload: FranchiseUpdatePayload,
  ): Observable<MasterFranchise> {
    return this.http.put<MasterFranchise>(
      `${this.baseUrl}/entities/franchises/${franchiseId}`,
      payload,
    );
  }

  deleteFranchise(franchiseId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/entities/franchises/${franchiseId}`);
  }

  searchLabels(query: string, limit = 20): Observable<MasterLabel[]> {
    let params = new HttpParams().set('limit', limit.toString());
    if (query && query.trim()) params = params.set('query', query.trim());
    return this.http.get<MasterLabel[]>(`${this.baseUrl}/entities/labels`, { params });
  }

  getLabelDetail(labelId: string): Observable<MasterLabel> {
    return this.http.get<MasterLabel>(`${this.baseUrl}/entities/labels/${labelId}`);
  }

  getLabelAlbums(labelId: string): Observable<AlbumSummary[]> {
    return this.http.get<AlbumSummary[]>(`${this.baseUrl}/entities/labels/${labelId}/albums`);
  }

  createLabel(payload: LabelCreatePayload): Observable<MasterLabel> {
    return this.http.post<MasterLabel>(`${this.baseUrl}/entities/labels`, payload);
  }

  updateLabel(labelId: string, payload: LabelUpdatePayload): Observable<MasterLabel> {
    return this.http.put<MasterLabel>(`${this.baseUrl}/entities/labels/${labelId}`, payload);
  }

  deleteLabel(labelId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/entities/labels/${labelId}`);
  }

  searchPublishers(query: string, limit = 20): Observable<MasterPublisher[]> {
    let params = new HttpParams().set('limit', limit.toString());
    if (query && query.trim()) params = params.set('query', query.trim());
    return this.http.get<MasterPublisher[]>(`${this.baseUrl}/entities/publishers`, { params });
  }

  getPublisherDetail(publisherId: string): Observable<MasterPublisher> {
    return this.http.get<MasterPublisher>(`${this.baseUrl}/entities/publishers/${publisherId}`);
  }

  getPublisherAlbums(publisherId: string): Observable<AlbumSummary[]> {
    return this.http.get<AlbumSummary[]>(
      `${this.baseUrl}/entities/publishers/${publisherId}/albums`,
    );
  }

  createPublisher(payload: PublisherCreatePayload): Observable<MasterPublisher> {
    return this.http.post<MasterPublisher>(`${this.baseUrl}/entities/publishers`, payload);
  }

  updatePublisher(
    publisherId: string,
    payload: PublisherUpdatePayload,
  ): Observable<MasterPublisher> {
    return this.http.put<MasterPublisher>(
      `${this.baseUrl}/entities/publishers/${publisherId}`,
      payload,
    );
  }

  deletePublisher(publisherId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/entities/publishers/${publisherId}`);
  }

  getLabels(query: string): Observable<string[]> {
    return this.searchLabels(query).pipe(map((list) => list.map((l) => l.name_original)));
  }

  getPublishers(query: string): Observable<string[]> {
    return this.searchPublishers(query).pipe(map((list) => list.map((p) => p.name_original)));
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
}
