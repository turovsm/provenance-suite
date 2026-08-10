import { Injectable, computed, inject, signal } from '@angular/core';
import { catchError, of } from 'rxjs';
import { ALBUM_REPOSITORY_PORT } from '../../../core/tokens/album.token';
import {
  EventCreatePayload,
  EventUpdatePayload,
  MasterEvent,
} from '../../../domain/models/music.model';
import { extractErrorMessage } from '../../../shared/utils/error-extractor';

@Injectable({
  providedIn: 'root',
})
export class EventStateEngine {
  private readonly repo = inject(ALBUM_REPOSITORY_PORT);

  private readonly eventsSignal = signal<MasterEvent[]>([]);
  private readonly loadingSignal = signal<boolean>(false);
  private readonly submittingSignal = signal<boolean>(false);
  private readonly errorSignal = signal<string | null>(null);
  private readonly searchQuerySignal = signal<string>('');

  readonly events = computed(() => this.eventsSignal());
  readonly isLoading = computed(() => this.loadingSignal());
  readonly isSubmitting = computed(() => this.submittingSignal());
  readonly error = computed(() => this.errorSignal());
  readonly searchQuery = computed(() => this.searchQuerySignal());

  setSearchQuery(query: string): void {
    this.searchQuerySignal.set(query);
    this.queryEvents();
  }

  queryEvents(): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);

    this.repo
      .searchEvents(this.searchQuerySignal(), 100)
      .pipe(
        catchError((err) => {
          const msg = extractErrorMessage(err, 'Failed to fetch events registry.');
          this.errorSignal.set(msg);
          this.loadingSignal.set(false);
          return of([]);
        }),
      )
      .subscribe((res) => {
        this.eventsSignal.set(res);
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
