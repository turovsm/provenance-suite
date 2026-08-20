import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { EventDateRange, MasterEvent } from '../../../../domain/models/music.model';
import { SelectOption } from '../../../../shared/components/custom-select/custom-select.component';
import { EmptyStateComponent } from '../../../../shared/components/empty-state/empty-state.component';
import { PaginationBarComponent } from '../../../../shared/components/pagination-bar/pagination-bar.component';
import { SearchInputComponent } from '../../../../shared/components/search-input/search-input.component';
import { AuthStateEngine } from '../../../auth/state/auth.state';
import { EventStateEngine } from '../../state/event.state';
import { EventFormModalComponent } from '../event-form-modal/event-form-modal.component';

const ALL_STATUSES = ['HELD', 'UPCOMING', 'POSTPONED', 'CANCELLED', 'UNKNOWN'];

const PAGE_SIZE_OPTIONS: SelectOption[] = [
  { label: '25 / page', value: '25' },
  { label: '50 / page', value: '50' },
  { label: '100 / page', value: '100' },
];

@Component({
  selector: 'app-event-list',
  standalone: true,
  imports: [
    EventFormModalComponent,
    FormsModule,
    PaginationBarComponent,
    SearchInputComponent,
    EmptyStateComponent,
  ],
  styleUrls: ['./event-list.component.css'],
  templateUrl: './event-list.component.html',
})
export class EventListComponent implements OnInit {
  protected readonly state = inject(EventStateEngine);
  protected readonly authState = inject(AuthStateEngine);

  protected isAddModalOpen = false;
  protected readonly eventToEdit = signal<MasterEvent | null>(null);

  protected readonly availableStatuses = ALL_STATUSES;
  protected readonly pageSizeOptions = PAGE_SIZE_OPTIONS;

  ngOnInit(): void {
    this.state.queryEvents();
  }

  protected handleSearchChange(term: string): void {
    this.state.setSearchQuery(term);
  }

  protected toggleSort(field: string): void {
    if (this.state.sortField() === field) {
      const nextOrder = this.state.sortOrder() === 'asc' ? 'desc' : 'asc';
      this.state.setSorting(field, nextOrder);
    } else {
      this.state.setSorting(field, 'asc');
    }
  }

  protected toggleStatusFilter(statusStr: string): void {
    const current = new Set(this.state.selectedStatuses());
    if (current.has(statusStr)) {
      if (current.size > 1) {
        current.delete(statusStr);
      }
    } else {
      current.add(statusStr);
    }
    this.state.setStatusFilter(current);
  }

  protected handleDateFromChange(value: string): void {
    this.state.setDateRange(value, this.state.dateTo());
  }

  protected handleDateToChange(value: string): void {
    this.state.setDateRange(this.state.dateFrom(), value);
  }

  protected handlePageSizeChange(size: number): void {
    this.state.setPageSize(size);
  }

  protected resetFilters(): void {
    this.state.resetFilters();
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
    const toSlash = (d: string | null | undefined) => (d ? d.replace(/[-.]/g, '/') : '');

    const formatRange = (startStr?: string | null, endStr?: string | null) => {
      const start = toSlash(startStr);
      const end = toSlash(endStr);
      if (!start && !end) return '';
      if (start && end && start !== end) return `${start} – ${end}`;
      return start || end || '';
    };

    const primaryRange = formatRange(ev.start_date, ev.end_date) || 'TBA / Unscheduled';

    if (ev.date_history && ev.date_history.length > 1) {
      const historyStr = ev.date_history
        .map((step: EventDateRange) => formatRange(step.start_date, step.end_date))
        .filter(Boolean)
        .join(' → ');
      if (historyStr) {
        return historyStr;
      }
    }

    if (ev.additional_dates && ev.additional_dates.length > 0) {
      const extraStr = ev.additional_dates
        .map((step: EventDateRange) => formatRange(step.start_date, step.end_date))
        .filter(Boolean)
        .join(' | ');
      if (extraStr) {
        return `${primaryRange} | ${extraStr}`;
      }
    }

    const origRange = formatRange(ev.original_start_date, ev.original_end_date);
    if (origRange && origRange !== primaryRange) {
      return `${primaryRange} (Was: ${origRange})`;
    }

    return primaryRange;
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
      case 'UNKNOWN':
        return 'status-unknown';
      default:
        return 'status-held';
    }
  }
}
