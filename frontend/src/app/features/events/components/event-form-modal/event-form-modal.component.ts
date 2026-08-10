import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  inject,
} from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MasterEvent } from '../../../../domain/models/music.model';
import {
  CustomSelectComponent,
  SelectOption,
} from '../../../../shared/components/custom-select/custom-select.component';
import { EventStateEngine } from '../../state/event.state';

const EVENT_STATUS_OPTIONS: SelectOption[] = [
  { label: 'Held (Official)', value: 'HELD' },
  { label: 'Upcoming', value: 'UPCOMING' },
  { label: 'Postponed', value: 'POSTPONED' },
  { label: 'Cancelled', value: 'CANCELLED' },
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
    start_date: [null],
    end_date: [null],
    status: ['HELD', [Validators.required]],
  });

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['eventToEdit']) {
      if (this.eventToEdit) {
        this.form.patchValue({
          short_name: this.eventToEdit.short_name,
          full_name: this.eventToEdit.full_name || '',
          start_date: this.eventToEdit.start_date || null,
          end_date: this.eventToEdit.end_date || null,
          status: this.eventToEdit.status || 'HELD',
        });
      } else {
        this.form.reset({ status: 'HELD' });
      }
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
    const payload = {
      short_name: raw.short_name.trim(),
      full_name: raw.full_name?.trim() || null,
      start_date: raw.start_date || null,
      end_date: raw.end_date || null,
      status: raw.status || 'HELD',
    };

    if (this.eventToEdit) {
      this.state.updateEvent(this.eventToEdit.id, payload, () => this.closeModal());
    } else {
      this.state.createEvent(payload, () => this.closeModal());
    }
  }
}
