import { Component, EventEmitter, inject, Output, HostListener, signal } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { AlbumStateEngine } from '../../state/album.state';
import { AlbumIngestRequest, LibraryCategory } from '../../../../domain/models/music.model';

@Component({
  selector: 'app-album-form-modal',
  standalone: true,
  imports: [ReactiveFormsModule],
  styleUrls: ['./album-form-modal.component.css'],
  templateUrl: './album-form-modal.component.html',
})
export class AlbumFormModalComponent {
  @Output() closed = new EventEmitter<void>();

  protected readonly state = inject(AlbumStateEngine);
  private readonly fb = inject(FormBuilder);

  protected coverBase64: string | null = null;
  protected coverMimeType = 'image/jpeg';

  protected readonly categoriesList: LibraryCategory[] = [
    'Doujin',
    'Vocaloid',
    'VNs',
    'JPop',
    'Anime',
    'GameOST',
    'Soundtrack',
    'Electronic',
    'Rock',
    'Pop',
    'Classical',
  ];
  protected readonly mediaTypes = ['CD', 'DVD', 'BD', 'Cassette', 'Vinyl', 'Web'];
  protected readonly containerFormats = ['Tracks', 'ISO', 'MDF', 'BIN_CUE', 'CDI', 'IMG', 'VOB'];
  protected readonly logTypes = ['EAC', 'XLD', 'EZCD', 'CUERipper', 'cyanrip', 'whipper'];
  protected readonly audioCodecs = [
    'FLAC',
    'MP3',
    'ALAC',
    'AAC',
    'PCM',
    'AC3',
    'DTS',
    'WMA',
    'WavPack',
  ];
  protected readonly videoCodecs = ['MPEG2', 'H264', 'HEVC', 'VC1'];
  protected readonly bitrateModes = ['CBR', 'VBR', 'ABR'];

  protected selectedCategories: LibraryCategory[] = ['Doujin'];

  protected readonly activeDropdownId = signal<string | null>(null);

  protected readonly form: FormGroup = this.fb.group({
    title_original: ['', [Validators.required, Validators.maxLength(512)]],
    title_translated: ['', [Validators.maxLength(512)]],
    original_folder_name: ['', [Validators.required, Validators.maxLength(1024)]],
    release_date: [''],
    label: ['', [Validators.maxLength(255)]],
    publisher: ['', [Validators.maxLength(255)]],
    storage_drive: ['', [Validators.maxLength(64)]],
    relative_path: ['', [Validators.maxLength(1024)]],
    discs: this.fb.array([this.createDiscGroup(1)]),
    archives: this.fb.array([]),
    external_links: this.fb.array([]),
  });

  get discs(): FormArray {
    return this.form.get('discs') as FormArray;
  }
  get archives(): FormArray {
    return this.form.get('archives') as FormArray;
  }
  get externalLinks(): FormArray {
    return this.form.get('external_links') as FormArray;
  }

  getTracks(discIndex: number): FormArray {
    return this.discs.at(discIndex).get('tracks') as FormArray;
  }

  getArchiveLinks(archiveIndex: number): FormArray {
    return this.archives.at(archiveIndex).get('links') as FormArray;
  }

  protected toggleDropdown(id: string, event: MouseEvent): void {
    event.stopPropagation();
    this.activeDropdownId.set(this.activeDropdownId() === id ? null : id);
  }

  protected selectControlValue(control: any, value: any): void {
    control.setValue(value);
    control.markAsDirty();
    this.activeDropdownId.set(null);
  }

  @HostListener('document:click')
  protected closeAllDropdowns(): void {
    this.activeDropdownId.set(null);
  }

  protected toggleCategory(cat: LibraryCategory): void {
    if (this.selectedCategories.includes(cat)) {
      if (this.selectedCategories.length > 1) {
        this.selectedCategories = this.selectedCategories.filter((c) => c !== cat);
      }
    } else {
      this.selectedCategories.push(cat);
    }
  }

  protected isCategorySelected(cat: LibraryCategory): boolean {
    return this.selectedCategories.includes(cat);
  }

  private createDiscGroup(discNumber: number): FormGroup {
    return this.fb.group({
      disc_number: [discNumber, [Validators.required, Validators.min(1)]],
      media_type: ['CD', Validators.required],
      container_format: ['Tracks', Validators.required],
      catalog_number: [''],
      log_type: [''],
      log_score: [null, [Validators.max(100)]],
      tracks: this.fb.array([this.createTrackGroup(1)]),
    });
  }

  private createTrackGroup(trackNumber: number): FormGroup {
    return this.fb.group({
      track_number: [trackNumber, [Validators.required, Validators.min(1)]],
      title_original: ['', Validators.required],
      title_translated: [''],
      duration_seconds: [null, Validators.min(0)],
      audio_codec: ['FLAC'],
      video_codec: [''],
      bit_depth: [null, Validators.min(0)],
      sample_rate: [null, Validators.min(0)],
      bitrate_kbps: [null, Validators.min(0)],
      bitrate_mode: [''],
    });
  }

  private createArchiveGroup(): FormGroup {
    return this.fb.group({
      archive_name: ['', Validators.required],
      encryption_password: [''],
      file_size_bytes: [null, Validators.min(0)],
      hash_sha256: ['', Validators.maxLength(64)],
      links: this.fb.array([this.createArchiveLinkGroup()]),
    });
  }

  private createArchiveLinkGroup(): FormGroup {
    return this.fb.group({
      provider_name: ['Mega', Validators.required],
      download_url: ['', Validators.required],
      is_active: [true],
    });
  }

  private createExternalLinkGroup(): FormGroup {
    return this.fb.group({
      site_name: ['VGMdb', Validators.required],
      url: ['', Validators.required],
      remote_item_id: [''],
    });
  }

  protected addDisc(): void {
    this.discs.push(this.createDiscGroup(this.discs.length + 1));
  }
  protected removeDisc(index: number): void {
    if (this.discs.length > 1) this.discs.removeAt(index);
  }

  protected addTrack(discIndex: number): void {
    const tracksArray = this.getTracks(discIndex);
    tracksArray.push(this.createTrackGroup(tracksArray.length + 1));
  }
  protected removeTrack(discIndex: number, trackIndex: number): void {
    const tracksArray = this.getTracks(discIndex);
    if (tracksArray.length > 1) tracksArray.removeAt(trackIndex);
  }

  protected addArchive(): void {
    this.archives.push(this.createArchiveGroup());
  }
  protected removeArchive(index: number): void {
    this.archives.removeAt(index);
  }

  protected addArchiveLink(archiveIndex: number): void {
    this.getArchiveLinks(archiveIndex).push(this.createArchiveLinkGroup());
  }
  protected removeArchiveLink(archiveIndex: number, linkIndex: number): void {
    this.getArchiveLinks(archiveIndex).removeAt(linkIndex);
  }

  protected addExternalLink(): void {
    this.externalLinks.push(this.createExternalLinkGroup());
  }
  protected removeExternalLink(index: number): void {
    this.externalLinks.removeAt(index);
  }

  protected handleCoverSelected(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.coverMimeType = file.type || 'image/jpeg';
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      this.coverBase64 = result.includes(',') ? result.split(',')[1] : result;
    };
    reader.readAsDataURL(file);
  }

  protected handleBackdropClick(event: MouseEvent): void {
    if (event.target === event.currentTarget) this.closeModal();
  }

  protected closeModal(): void {
    this.closed.emit();
  }

  protected handleSubmit(): void {
    if (this.form.invalid || this.selectedCategories.length === 0) {
      this.form.markAllAsTouched();
      return;
    }

    const formVal = this.form.value;
    const payload: AlbumIngestRequest = {
      title_original: formVal.title_original,
      title_translated: formVal.title_translated || null,
      categories: this.selectedCategories,
      original_folder_name: formVal.original_folder_name,
      release_date: formVal.release_date || null,
      label: formVal.label || null,
      publisher: formVal.publisher || null,
      storage_drive: formVal.storage_drive || null,
      relative_path: formVal.relative_path || null,
      discs: formVal.discs.map((d: any) => ({
        ...d,
        log_type: d.log_type || null,
        catalog_number: d.catalog_number || null,
        tracks: d.tracks.map((t: any) => ({
          ...t,
          title_translated: t.title_translated || null,
          video_codec: t.video_codec || null,
          bitrate_mode: t.bitrate_mode || null,
        })),
      })),
      archives: formVal.archives.map((a: any) => ({
        ...a,
        encryption_password: a.encryption_password || null,
        hash_sha256: a.hash_sha256 || null,
      })),
      external_links: formVal.external_links.map((el: any) => ({
        ...el,
        remote_item_id: el.remote_item_id || null,
      })),
      cover: this.coverBase64
        ? {
            image_data: this.coverBase64,
            mime_type: this.coverMimeType,
            width: 500,
            height: 500,
          }
        : null,
    };

    this.state.ingestAlbum(payload, () => this.closeModal());
  }
}
