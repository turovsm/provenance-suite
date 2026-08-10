import {
  Component,
  DestroyRef,
  EventEmitter,
  HostListener,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  Output,
  SimpleChanges,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormArray, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { AlbumDetailResponse } from '../../../../domain/models/music.model';
import { FormTab } from '../../models/album-form.model';
import { AlbumDraftService } from '../../services/album-draft.service';
import { AlbumFormBuilderService } from '../../services/album-form-builder.service';
import { AlbumPayloadMapperService } from '../../services/album-payload-mapper.service';
import { CoverListService } from '../../services/cover-list.service';
import { AlbumStateEngine } from '../../state/album.state';
import { ArchivesTabComponent } from './tabs/archives-tab.component';
import { BasicInfoTabComponent } from './tabs/basic-info-tab.component';
import { CoversTabComponent } from './tabs/covers-tab.component';
import { DiscsTabComponent } from './tabs/discs-tab.component';

@Component({
  selector: 'app-album-form-modal',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    BasicInfoTabComponent,
    DiscsTabComponent,
    CoversTabComponent,
    ArchivesTabComponent,
  ],
  providers: [CoverListService],
  styleUrls: ['./album-form-modal.component.css'],
  templateUrl: './album-form-modal.component.html',
})
export class AlbumFormModalComponent implements OnInit, OnChanges, OnDestroy {
  @Input() albumToEdit?: AlbumDetailResponse | null = null;
  @Output() closed = new EventEmitter<void>();

  protected readonly state = inject(AlbumStateEngine);
  protected readonly coverService = inject(CoverListService);
  private readonly builder = inject(AlbumFormBuilderService);
  private readonly draftService = inject(AlbumDraftService);
  private readonly payloadMapper = inject(AlbumPayloadMapperService);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly currentTab = signal<FormTab>('basic');
  protected readonly form: FormGroup = this.builder.buildAlbumForm();

  get discs(): FormArray {
    return this.builder.discsOf(this.form);
  }
  get archives(): FormArray {
    return this.builder.archivesOf(this.form);
  }
  get externalLinks(): FormArray {
    return this.builder.externalLinksOf(this.form);
  }

  @HostListener('window:dragover', ['$event'])
  protected onWindowDragOver(event: DragEvent): void {
    event.preventDefault();
  }

  @HostListener('window:drop', ['$event'])
  protected onWindowDrop(event: DragEvent): void {
    event.preventDefault();
  }

  ngOnInit(): void {
    if (this.albumToEdit) {
      this.populateFormForEditing(this.albumToEdit);
    } else {
      this.initDefaultForm();
      this.restoreDraft();
    }

    this.form.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.persistDraftIfCreating());
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['albumToEdit'] && !changes['albumToEdit'].firstChange) {
      if (this.albumToEdit) {
        this.populateFormForEditing(this.albumToEdit);
      } else {
        this.initDefaultForm();
        this.restoreDraft();
      }
    }
  }

  ngOnDestroy(): void {
    this.coverService.revokeAll();
  }

  protected switchTab(tab: FormTab): void {
    this.currentTab.set(tab);
  }

  private initDefaultForm(): void {
    this.builder.resetToDefaults(this.form);
    this.coverService.reset();
  }

  private populateFormForEditing(album: AlbumDetailResponse): void {
    this.builder.resetToDefaults(this.form);
    this.builder.populateFromAlbum(this.form, album);
    this.coverService.hydrateFromAlbum(album.covers ?? []);
  }

  private persistDraftIfCreating(): void {
    if (this.albumToEdit) return;
    this.draftService.persist({
      formValue: this.form.value,
    });
  }

  private restoreDraft(): void {
    const draft = this.draftService.restore();
    if (!draft) return;
    this.builder.applyDraftFormValue(this.form, draft.formValue);
  }

  protected resetCurrentTab(): void {
    const tab = this.currentTab();
    if (tab === 'basic') {
      this.form.patchValue({
        title_original: '',
        aliases: [],
        album_artist_aliases: [],
        franchise_aliases: [],
        original_folder_name: '',
        release_year: null,
        release_month: null,
        release_day: null,
        label: '',
        publisher: '',
        storage_drive: '',
        relative_path: '',
        event_id: null,
        franchise_id: null,
        album_artist_id: null,
      });
    } else if (tab === 'discs') {
      this.discs.clear();
      this.discs.push(this.builder.createDiscGroup({ disc_number: 1 }));
    } else if (tab === 'covers') {
      this.coverService.reset();
    } else if (tab === 'archives') {
      this.archives.clear();
      this.externalLinks.clear();
    }
    this.persistDraftIfCreating();
  }

  protected resetEntireForm(): void {
    if (confirm('Are you sure you want to reset all form sections and clear active draft?')) {
      this.draftService.clear();
      this.initDefaultForm();
    }
  }

  protected closeModal(): void {
    this.closed.emit();
  }

  protected async handleSubmit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const prepareCovers = await Promise.all(
      this.coverService.covers().map(async (item) => {
        if (item.base64) return item;
        if (item.file) {
          const base64 = await this.fileToBase64(item.file);
          return { ...item, base64 };
        }
        return item;
      }),
    );

    const payload = this.payloadMapper.toIngestRequest(this.form.value, prepareCovers);

    this.state.ingestAlbum(payload, () => {
      this.draftService.clear();
      this.closeModal();
    });
  }

  private fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        resolve(result.includes(',') ? result.split(',')[1] : result);
      };
      reader.onerror = (err) => reject(err);
      reader.readAsDataURL(file);
    });
  }
}
