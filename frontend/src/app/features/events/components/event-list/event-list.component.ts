import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { MasterEvent } from '../../../../domain/models/music.model';
import { AuthStateEngine } from '../../../auth/state/auth.state';
import { EventStateEngine } from '../../state/event.state';
import { EventFormModalComponent } from '../event-form-modal/event-form-modal.component';

@Component({
  selector: 'app-event-list',
  standalone: true,
  imports: [EventFormModalComponent],
  styleUrls: ['./event-list.component.css'],
  templateUrl: './event-list.component.html',
})
export class EventListComponent implements OnInit, OnDestroy {
  protected readonly state = inject(EventStateEngine);
  protected readonly authState = inject(AuthStateEngine);

  protected isAddModalOpen = false;
  protected readonly eventToEdit = signal<MasterEvent | null>(null);

  private readonly searchInput$ = new Subject<string>();
  private searchSubscription?: Subscription;

  ngOnInit(): void {
    this.searchSubscription = this.searchInput$
      .pipe(debounceTime(300), distinctUntilChanged())
      .subscribe((term) => {
        this.state.setSearchQuery(term);
      });

    this.state.queryEvents();
  }

  ngOnDestroy(): void {
    this.searchSubscription?.unsubscribe();
  }

  protected handleSearchInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.searchInput$.next(value);
  }

  protected openAddModal(): void {
    this.eventToEdit.set(null);
    this.isAddModalOpen = true;
  }

  protected handleEditEvent(event: MasterEvent): void {
    this.eventToEdit.set(event);
    this.isAddModalOpen = true;
  }

  protected handleDeleteEvent(event: MasterEvent): void {
    if (confirm(`Remove event "${event.short_name}" from registry?`)) {
      this.state.deleteEvent(event.id);
    }
  }

  protected closeAddModal(): void {
    this.isAddModalOpen = false;
    this.eventToEdit.set(null);
  }

  protected formatEventDateRange(ev: MasterEvent): string {
    if (!ev.start_date && !ev.end_date) return 'TBA / Unscheduled';
    if (ev.start_date && ev.end_date && ev.start_date !== ev.end_date) {
      return `${ev.start_date} – ${ev.end_date}`;
    }
    return ev.start_date || ev.end_date || 'Unscheduled';
  }

  protected getStatusClass(statusStr: string): string {
    switch (statusStr.toUpperCase()) {
      case 'HELD':
        return 'status-held';
      case 'UPCOMING':
        return 'status-upcoming';
      case 'POSTPONED':
        return 'status-postponed';
      case 'CANCELLED':
        return 'status-cancelled';
      default:
        return 'status-held';
    }
  }
}
