import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  inject,
} from '@angular/core';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { EventDateRange, MasterEvent } from '../../../../domain/models/music.model';
import {
  CustomSelectComponent,
  SelectOption,
} from '../../../../shared/components/custom-select/custom-select.component';
import { fuzzyDateValidator } from '../../../../shared/validators/fuzzy-date.validator';
import { EventStateEngine } from '../../state/event.state';

const EVENT_STATUS_OPTIONS: SelectOption[] = [
  { label: 'Held (Official)', value: 'HELD' },
  { label: 'Upcoming', value: 'UPCOMING' },
  { label: 'Postponed', value: 'POSTPONED' },
  { label: 'Cancelled', value: 'CANCELLED' },
  { label: 'Unknown Date', value: 'UNKNOWN' },
];

@Component({
  selector: 'app-event-form-modal',
  standalone: true,
  imports: [ReactiveFormsModule, CustomSelectComponent],
  styleUrls: ['./event-form-modal.component.css'],
  templateUrl: './event-form-modal.component.html',
})
export class EventFormModalComponent implements OnChanges {
  @Input() eventToEdit?: MasterEvent | null = null;
  @Output() closed = new EventEmitter<void>();

  protected readonly state = inject(EventStateEngine);
  private readonly fb = inject(FormBuilder);

  protected readonly statusOptions = EVENT_STATUS_OPTIONS;

  protected readonly form: FormGroup = this.fb.group({
    short_name: ['', [Validators.required, Validators.maxLength(128)]],
    full_name: ['', [Validators.maxLength(512)]],
    start_date: [null, [fuzzyDateValidator()]],
    end_date: [null, [fuzzyDateValidator()]],
    original_start_date: [null, [fuzzyDateValidator()]],
    original_end_date: [null, [fuzzyDateValidator()]],
    date_history: this.fb.array([]),
    additional_dates: this.fb.array([]),
    status: ['HELD', [Validators.required]],
  });

  get dateHistoryArray(): FormArray {
    return this.form.get('date_history') as FormArray;
  }

  get additionalDatesArray(): FormArray {
    return this.form.get('additional_dates') as FormArray;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['eventToEdit']) {
      this.resetAndPopulate();
    }
  }

  private formatToSlash(d: string | null | undefined): string {
    if (!d) return '';
    return d.trim().replace(/[-.]/g, '/');
  }

  private formatToDash(d: string | null | undefined): string | null {
    if (!d) return null;
    const trimmed = d.trim().replace(/[/.]/g, '-');
    return trimmed || null;
  }

  private createDateRangeGroup(range?: EventDateRange): FormGroup {
    return this.fb.group({
      start_date: [this.formatToSlash(range?.start_date), [fuzzyDateValidator()]],
      end_date: [this.formatToSlash(range?.end_date), [fuzzyDateValidator()]],
    });
  }

  protected addHistoryStep(): void {
    this.dateHistoryArray.push(this.createDateRangeGroup());
  }

  protected removeHistoryStep(index: number): void {
    this.dateHistoryArray.removeAt(index);
  }

  protected addAdditionalDate(): void {
    this.additionalDatesArray.push(this.createDateRangeGroup());
  }

  protected removeAdditionalDate(index: number): void {
    this.additionalDatesArray.removeAt(index);
  }

  private resetAndPopulate(): void {
    this.dateHistoryArray.clear();
    this.additionalDatesArray.clear();

    if (this.eventToEdit) {
      this.form.patchValue({
        short_name: this.eventToEdit.short_name,
        full_name: this.eventToEdit.full_name || '',
        start_date: this.formatToSlash(this.eventToEdit.start_date),
        end_date: this.formatToSlash(this.eventToEdit.end_date),
        original_start_date: this.formatToSlash(this.eventToEdit.original_start_date),
        original_end_date: this.formatToSlash(this.eventToEdit.original_end_date),
        status: this.eventToEdit.status || 'HELD',
      });

      (this.eventToEdit.date_history ?? []).forEach((item) => {
        this.dateHistoryArray.push(this.createDateRangeGroup(item));
      });

      (this.eventToEdit.additional_dates ?? []).forEach((item) => {
        this.additionalDatesArray.push(this.createDateRangeGroup(item));
      });
    } else {
      this.form.reset({ status: 'HELD' });
    }
  }

  protected closeModal(): void {
    this.closed.emit();
  }

  protected handleSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const raw = this.form.value;
    const mapRange = (r: { start_date?: string | null; end_date?: string | null }) => ({
      start_date: this.formatToDash(r.start_date),
      end_date: this.formatToDash(r.end_date),
    });

    const payload = {
      short_name: raw.short_name.trim(),
      full_name: raw.full_name?.trim() || null,
      start_date: this.formatToDash(raw.start_date),
      end_date: this.formatToDash(raw.end_date),
      original_start_date: this.formatToDash(raw.original_start_date),
      original_end_date: this.formatToDash(raw.original_end_date),
      date_history: (raw.date_history || []).map(mapRange),
      additional_dates: (raw.additional_dates || []).map(mapRange),
      status: raw.status || 'HELD',
    };

    if (this.eventToEdit) {
      this.state.updateEvent(this.eventToEdit.id, payload, () => this.closeModal());
    } else {
      this.state.createEvent(payload, () => this.closeModal());
    }
  }
}
