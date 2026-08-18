import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { EntitySummary } from '../../../../domain/models/music.model';
import { AliasesChipInputComponent } from '../../../../shared/components/aliases-chip-input/aliases-chip-input.component';
import {
  CustomSelectComponent,
  SelectOption,
} from '../../../../shared/components/custom-select/custom-select.component';
import { EntityStateEngine } from '../../state/entity.state';

const ENTITY_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Artist / Circle', value: 'artist' },
  { label: 'Media Franchise', value: 'franchise' },
  { label: 'Record Label', value: 'label' },
  { label: 'Publisher / Distributor', value: 'publisher' },
];

@Component({
  selector: 'app-entity-form-modal',
  standalone: true,
  imports: [ReactiveFormsModule, CustomSelectComponent, AliasesChipInputComponent],
  styleUrls: ['./entity-form-modal.component.css'],
  templateUrl: './entity-form-modal.component.html',
})
export class EntityFormModalComponent implements OnChanges {
  @Input() entityToEdit?: EntitySummary | null = null;
  @Input() defaultType = 'artist';
  @Output() closed = new EventEmitter<void>();

  protected readonly state = inject(EntityStateEngine);
  private readonly fb = inject(FormBuilder);

  protected readonly entityTypeOptions = ENTITY_TYPE_OPTIONS;
  protected readonly imagePreviewUrl = signal<string | null>(null);
  protected base64ImageData: string | null = null;

  protected readonly form: FormGroup = this.fb.group({
    entity_type: [this.defaultType, Validators.required],
    name_original: ['', [Validators.required, Validators.maxLength(512)]],
    aliases: [[]],
    franchise_type: ['Game'],
    description: [''],
  });

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['entityToEdit']) {
      this.populateForm();
    }
  }

  private populateForm(): void {
    if (this.entityToEdit) {
      this.form.patchValue({
        entity_type: this.entityToEdit.entity_type,
        name_original: this.entityToEdit.name_original,
        aliases: this.entityToEdit.aliases ?? [],
        franchise_type: this.entityToEdit.franchise_type || 'Game',
        description: this.entityToEdit.description || '',
      });
      this.form.get('entity_type')?.disable();
      this.imagePreviewUrl.set(this.entityToEdit.image_url || null);
    } else {
      this.form.reset({
        entity_type: this.defaultType,
        franchise_type: 'Game',
        aliases: [],
      });
      this.form.get('entity_type')?.enable();
      this.imagePreviewUrl.set(null);
    }
    this.base64ImageData = null;
  }

  protected handleFileSelected(event: Event): void {
    const files = (event.target as HTMLInputElement).files;
    if (!files?.length) return;
    const file = files[0];
    this.imagePreviewUrl.set(URL.createObjectURL(file));

    const reader = new FileReader();
    reader.onload = () => {
      const resStr = reader.result as string;
      this.base64ImageData = resStr.includes(',') ? resStr.split(',')[1] : resStr;
    };
    reader.readAsDataURL(file);
  }

  protected closeModal(): void {
    this.closed.emit();
  }

  protected handleSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const raw = this.form.getRawValue();
    const entityType = this.entityToEdit ? this.entityToEdit.entity_type : raw.entity_type;

    if (this.entityToEdit) {
      const id = this.entityToEdit.id;
      if (entityType === 'artist') {
        this.state.updateArtist(
          id,
          {
            name_original: raw.name_original,
            aliases: raw.aliases,
            description: raw.description,
            image_data: this.base64ImageData,
          },
          () => this.closeModal(),
        );
      } else if (entityType === 'franchise') {
        this.state.updateFranchise(
          id,
          {
            name_original: raw.name_original,
            aliases: raw.aliases,
            franchise_type: raw.franchise_type,
            description: raw.description,
            image_data: this.base64ImageData,
          },
          () => this.closeModal(),
        );
      } else if (entityType === 'label') {
        this.state.updateLabel(
          id,
          {
            name_original: raw.name_original,
            aliases: raw.aliases,
            description: raw.description,
            image_data: this.base64ImageData,
          },
          () => this.closeModal(),
        );
      } else if (entityType === 'publisher') {
        this.state.updatePublisher(
          id,
          {
            name_original: raw.name_original,
            aliases: raw.aliases,
            description: raw.description,
            image_data: this.base64ImageData,
          },
          () => this.closeModal(),
        );
      }
    } else {
      if (entityType === 'artist') {
        this.state.createArtist(
          {
            name_original: raw.name_original,
            aliases: raw.aliases,
            description: raw.description,
            image_data: this.base64ImageData,
          },
          () => this.closeModal(),
        );
      } else if (entityType === 'franchise') {
        this.state.createFranchise(
          {
            name_original: raw.name_original,
            aliases: raw.aliases,
            franchise_type: raw.franchise_type,
            description: raw.description,
            image_data: this.base64ImageData,
          },
          () => this.closeModal(),
        );
      } else if (entityType === 'label') {
        this.state.createLabel(
          {
            name_original: raw.name_original,
            aliases: raw.aliases,
            description: raw.description,
            image_data: this.base64ImageData,
          },
          () => this.closeModal(),
        );
      } else if (entityType === 'publisher') {
        this.state.createPublisher(
          {
            name_original: raw.name_original,
            aliases: raw.aliases,
            description: raw.description,
            image_data: this.base64ImageData,
          },
          () => this.closeModal(),
        );
      }
    }
  }
}
