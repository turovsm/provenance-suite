import { Component, Input, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
} from '@angular/forms';
import { ALBUM_REPOSITORY_PORT } from '../../../../../core/tokens/album.token';
import { CustomSelectComponent } from '../../../../../shared/components/custom-select/custom-select.component';
import { EntityAutocompleteComponent } from '../../../../../shared/components/entity-autocomplete/entity-autocomplete.component';
import { AutocompleteOption } from '../../../../../shared/models/autocomplete.model';
import {
  AUDIO_CODECS,
  BITRATE_MODE_OPTIONS,
  CONTAINER_FORMATS,
  LOG_TYPE_OPTIONS,
  MEDIA_TYPES,
  TRACK_ARTIST_ROLES,
  VIDEO_CODEC_OPTIONS,
} from '../../../constants/album-form-options';
import { DiscSeed } from '../../../models/album-form.model';
import { AlbumFormBuilderService } from '../../../services/album-form-builder.service';

@Component({
  selector: 'app-discs-tab',
  standalone: true,
  imports: [ReactiveFormsModule, FormsModule, CustomSelectComponent, EntityAutocompleteComponent],
  styleUrls: ['../album-form-modal.component.css'],
  templateUrl: './discs-tab.component.html',
})
export class DiscsTabComponent {
  @Input({ required: true }) discs!: FormArray;

  private readonly repo = inject(ALBUM_REPOSITORY_PORT);
  private readonly builder = inject(AlbumFormBuilderService);

  protected readonly mediaTypes = MEDIA_TYPES;
  protected readonly containerFormats = CONTAINER_FORMATS;
  protected readonly logTypeOptions = LOG_TYPE_OPTIONS;
  protected readonly audioCodecs = AUDIO_CODECS;
  protected readonly videoCodecOptions = VIDEO_CODEC_OPTIONS;
  protected readonly bitrateModeOptions = BITRATE_MODE_OPTIONS;
  protected readonly trackArtistRoles = TRACK_ARTIST_ROLES;

  protected readonly importSuccessMessage = signal<string | null>(null);
  protected readonly importErrorMessage = signal<string | null>(null);
  protected readonly showManualPaste = signal<boolean>(false);
  protected manualJsonText = '';

  getTracks(discIndex: number): FormArray {
    return this.discs.at(discIndex).get('tracks') as FormArray;
  }

  getTrackArtists(discIndex: number, trackIndex: number): FormArray {
    return this.getTracks(discIndex).at(trackIndex).get('artists') as FormArray;
  }

  protected addDisc(): void {
    this.discs.push(this.builder.createDiscGroup({ disc_number: this.discs.length + 1 }));
  }

  protected removeDisc(index: number): void {
    if (this.discs.length > 1) this.discs.removeAt(index);
  }

  private reindexTracks(discIndex: number): void {
    this.getTracks(discIndex).controls.forEach((control, idx) => {
      control.patchValue({ track_number: idx + 1 }, { emitEvent: false });
    });
  }

  protected addTrack(discIndex: number): void {
    const tracks = this.getTracks(discIndex);
    tracks.push(this.builder.createTrackGroup({ track_number: tracks.length + 1 }));
    this.reindexTracks(discIndex);
  }

  protected removeTrack(discIndex: number, trackIndex: number): void {
    const tracks = this.getTracks(discIndex);
    if (tracks.length > 1) {
      tracks.removeAt(trackIndex);
      this.reindexTracks(discIndex);
    }
  }

  protected addTrackArtist(discIndex: number, trackIndex: number): void {
    this.getTrackArtists(discIndex, trackIndex).push(
      this.builder.createArtistGroup({ role: 'Composer' }),
    );
  }

  protected removeTrackArtist(discIndex: number, trackIndex: number, artistIndex: number): void {
    this.getTrackArtists(discIndex, trackIndex).removeAt(artistIndex);
  }

  protected async importFromClipboard(): Promise<void> {
    this.importSuccessMessage.set(null);
    this.importErrorMessage.set(null);

    try {
      if (!navigator.clipboard || !navigator.clipboard.readText) {
        this.showManualPaste.set(true);
        return;
      }
      const text = await navigator.clipboard.readText();
      if (!text || !text.trim()) {
        this.importErrorMessage.set('Clipboard is empty or contains no text.');
        return;
      }
      this.processImportJson(text.trim());
    } catch {
      this.showManualPaste.set(true);
      this.importErrorMessage.set('Unable to access system clipboard directly.');
    }
  }

  protected applyManualJson(): void {
    if (!this.manualJsonText.trim()) return;
    this.processImportJson(this.manualJsonText.trim());
    this.manualJsonText = '';
    this.showManualPaste.set(false);
  }

  private processImportJson(jsonStr: string): void {
    this.importSuccessMessage.set(null);
    this.importErrorMessage.set(null);

    try {
      const parsed = JSON.parse(jsonStr);
      let seeds: DiscSeed[] = [];

      if (parsed && typeof parsed === 'object') {
        if (Array.isArray(parsed.discs)) {
          seeds = parsed.discs;
        } else if (Array.isArray(parsed)) {
          seeds = parsed;
        }
      }

      if (!seeds || seeds.length === 0) {
        this.importErrorMessage.set('Invalid format: expected JSON object with a "discs" array.');
        return;
      }

      this.builder.populateDiscsFromSeeds(this.discs, seeds);

      const totalTracks = seeds.reduce((acc, d) => acc + (d.tracks?.length || 0), 0);
      this.importSuccessMessage.set(
        `Successfully imported ${seeds.length} disc(s) and ${totalTracks} track(s) from export!`,
      );

      setTimeout(() => {
        this.importSuccessMessage.set(null);
      }, 5000);
    } catch {
      this.importErrorMessage.set('Failed to parse JSON string: invalid syntax.');
    }
  }

  protected handleTextFileSelected(
    event: Event | DragEvent,
    control: AbstractControl | null,
  ): void {
    event.preventDefault();
    event.stopPropagation();

    let file: File | null = null;
    if (event instanceof DragEvent && event.dataTransfer?.files?.length) {
      file = event.dataTransfer.files[0];
    } else if (event.target && (event.target as HTMLInputElement).files?.length) {
      file = (event.target as HTMLInputElement).files![0];
    }

    if (!file || !control) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      if (content !== undefined && content !== null) {
        control.setValue(content);
        control.markAsDirty();
      }
    };
    reader.readAsText(file);
  }

  protected handleTrackArtistSelected(
    discIndex: number,
    trackIndex: number,
    artistIndex: number,
    option: AutocompleteOption,
  ): void {
    const artistGroup = this.getTrackArtists(discIndex, trackIndex).at(artistIndex) as FormGroup;
    artistGroup.patchValue({ name_translated: option.subValue || '' });
  }

  protected refreshArtistTranslation(
    discIndex: number,
    trackIndex: number,
    artistIndex: number,
  ): void {
    const artistGroup = this.getTrackArtists(discIndex, trackIndex).at(artistIndex) as FormGroup;
    const nameOriginal = artistGroup.get('name_original')?.value?.trim();
    const nameTranslated = artistGroup.get('name_translated')?.value?.trim() || '';

    if (!nameOriginal) return;

    this.repo.createArtist(nameOriginal, nameTranslated).subscribe({
      next: (savedArtist) => {
        const updatedTranslation = savedArtist.name_translated || '';
        artistGroup.patchValue({ name_translated: updatedTranslation });
        this.propagateArtistTranslation(nameOriginal, updatedTranslation);
      },
      error: (err) => {
        console.error('Failed to sync artist translation:', err);
      },
    });
  }

  private propagateArtistTranslation(nameOriginal: string, nameTranslated: string): void {
    const targetLower = nameOriginal.trim().toLowerCase();

    this.discs.controls.forEach((discControl) => {
      const tracks = discControl.get('tracks') as FormArray;
      if (!tracks) return;

      tracks.controls.forEach((trackControl) => {
        const artists = trackControl.get('artists') as FormArray;
        if (!artists) return;

        artists.controls.forEach((artControl) => {
          const orig = artControl.get('name_original')?.value?.trim();
          if (orig && orig.toLowerCase() === targetLower) {
            artControl.patchValue({ name_translated: nameTranslated });
          }
        });
      });
    });
  }
}
