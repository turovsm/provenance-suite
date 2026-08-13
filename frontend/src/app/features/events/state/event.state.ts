import { Injectable, computed, inject, signal } from '@angular/core';
import { catchError, of } from 'rxjs';
import { ALBUM_REPOSITORY_PORT } from '../../../core/tokens/album.token';
import {
  EventCreatePayload,
  EventUpdatePayload,
  MasterEvent,
} from '../../../domain/models/music.model';
import { extractErrorMessage } from '../../../shared/utils/error-extractor';

const ALL_STATUSES = ['HELD', 'UPCOMING', 'POSTPONED', 'CANCELLED', 'UNKNOWN'];

@Injectable({
  providedIn: 'root',
})
export class EventStateEngine {
  private readonly repo = inject(ALBUM_REPOSITORY_PORT);

  private readonly eventsSignal = signal<MasterEvent[]>([]);
  private readonly totalCountSignal = signal<number>(0);
  private readonly loadingSignal = signal<boolean>(false);
  private readonly submittingSignal = signal<boolean>(false);
  private readonly errorSignal = signal<string | null>(null);

  private readonly searchQuerySignal = signal<string>('');
  private readonly selectedStatusesSignal = signal<Set<string>>(new Set(ALL_STATUSES));
  private readonly dateFromSignal = signal<string>('');
  private readonly dateToSignal = signal<string>('');
  private readonly sortFieldSignal = signal<string>('start_date');
  private readonly sortOrderSignal = signal<string>('desc');
  private readonly pageSignal = signal<number>(1);
  private readonly pageSizeSignal = signal<number>(50);

  readonly events = computed(() => this.eventsSignal());
  readonly totalCount = computed(() => this.totalCountSignal());
  readonly isLoading = computed(() => this.loadingSignal());
  readonly isSubmitting = computed(() => this.submittingSignal());
  readonly error = computed(() => this.errorSignal());
  readonly searchQuery = computed(() => this.searchQuerySignal());
  readonly selectedStatuses = computed(() => this.selectedStatusesSignal());
  readonly dateFrom = computed(() => this.dateFromSignal());
  readonly dateTo = computed(() => this.dateToSignal());
  readonly sortField = computed(() => this.sortFieldSignal());
  readonly sortOrder = computed(() => this.sortOrderSignal());
  readonly currentPage = computed(() => this.pageSignal());
  readonly pageSize = computed(() => this.pageSizeSignal());

  readonly totalPages = computed(
    () => Math.ceil(this.totalCountSignal() / this.pageSizeSignal()) || 1,
  );

  setSearchQuery(query: string): void {
    this.searchQuerySignal.set(query);
    this.pageSignal.set(1);
    this.queryEvents();
  }

  setStatusFilter(statuses: Set<string>): void {
    this.selectedStatusesSignal.set(statuses);
    this.pageSignal.set(1);
    this.queryEvents();
  }

  setDateRange(from: string, to: string): void {
    this.dateFromSignal.set(from);
    this.dateToSignal.set(to);
    this.pageSignal.set(1);
    this.queryEvents();
  }

  setSorting(field: string, order: string): void {
    this.sortFieldSignal.set(field);
    this.sortOrderSignal.set(order);
    this.queryEvents();
  }

  setPage(page: number): void {
    if (page < 1 || page > this.totalPages()) return;
    this.pageSignal.set(page);
    this.queryEvents();
  }

  setPageSize(size: number): void {
    this.pageSizeSignal.set(size);
    this.pageSignal.set(1);
    this.queryEvents();
  }

  resetFilters(): void {
    this.selectedStatusesSignal.set(new Set(ALL_STATUSES));
    this.dateFromSignal.set('');
    this.dateToSignal.set('');
    this.searchQuerySignal.set('');
    this.pageSignal.set(1);
    this.queryEvents();
  }

  queryEvents(): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);

    const limit = this.pageSizeSignal();
    const offset = (this.pageSignal() - 1) * limit;
    const statuses = Array.from(this.selectedStatusesSignal());

    this.repo
      .fetchEvents(
        this.searchQuerySignal(),
        statuses,
        this.dateFromSignal() || null,
        this.dateToSignal() || null,
        this.sortFieldSignal(),
        this.sortOrderSignal(),
        limit,
        offset,
      )
      .pipe(
        catchError((err) => {
          const msg = extractErrorMessage(err, 'Failed to fetch events registry.');
          this.errorSignal.set(msg);
          this.loadingSignal.set(false);
          return of({ items: [], total_count: 0, limit, offset });
        }),
      )
      .subscribe((res) => {
        this.eventsSignal.set(res.items);
        this.totalCountSignal.set(res.total_count);
        this.loadingSignal.set(false);
      });
  }

  createEvent(payload: EventCreatePayload, onSuccess?: () => void): void {
    this.submittingSignal.set(true);
    this.errorSignal.set(null);

    this.repo
      .createEventFull(payload)
      .pipe(
        catchError((err) => {
          const msg = extractErrorMessage(err, 'Failed to create event record.');
          this.errorSignal.set(msg);
          this.submittingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (!res) return;
        this.submittingSignal.set(false);
        this.queryEvents();
        if (onSuccess) onSuccess();
      });
  }

  updateEvent(eventId: string, payload: EventUpdatePayload, onSuccess?: () => void): void {
    this.submittingSignal.set(true);
    this.errorSignal.set(null);

    this.repo
      .updateEvent(eventId, payload)
      .pipe(
        catchError((err) => {
          const msg = extractErrorMessage(err, 'Failed to update event record.');
          this.errorSignal.set(msg);
          this.submittingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (!res) return;
        this.submittingSignal.set(false);
        this.queryEvents();
        if (onSuccess) onSuccess();
      });
  }

  deleteEvent(eventId: string): void {
    this.errorSignal.set(null);

    this.repo
      .deleteEvent(eventId)
      .pipe(
        catchError((err) => {
          const msg = extractErrorMessage(err, 'Deletion failed.');
          this.errorSignal.set(msg);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (res === null && this.errorSignal()) return;
        this.queryEvents();
      });
  }
}
