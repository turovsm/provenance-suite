import { Component, Input, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
} from '@angular/forms';
import { MasterArtist } from '../../../../../domain/models/music.model';
import { CustomSelectComponent } from '../../../../../shared/components/custom-select/custom-select.component';
import { AliasesChipInputComponent } from '../../../../../shared/components/aliases-chip-input/aliases-chip-input.component';
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
  imports: [
    ReactiveFormsModule,
    FormsModule,
    CustomSelectComponent,
    EntityAutocompleteComponent,
    AliasesChipInputComponent,
  ],
  styleUrls: ['../album-form-modal.component.css'],
  templateUrl: './discs-tab.component.html',
})
export class DiscsTabComponent {
  @Input({ required: true }) discs!: FormArray;

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

  protected handleTrackArtistSelected(
    dIdx: number,
    tIdx: number,
    taIdx: number,
    option: AutocompleteOption,
  ): void {
    const artistGroup = this.getTrackArtists(dIdx, tIdx).at(taIdx) as FormGroup;
    const raw = option.raw as MasterArtist;
    if (raw && Array.isArray(raw.aliases) && raw.aliases.length > 0) {
      artistGroup.patchValue({ aliases: raw.aliases });
      this.propagateArtistAliases(raw.name_original, raw.aliases);
    }

    const nameOriginal = raw?.name_original ?? artistGroup.get('name_original')?.value?.trim();
    if (nameOriginal) {
      const roleControl = artistGroup.get('role');
      if (roleControl && roleControl.value === 'Composer') {
        const commonRole = this.getMostCommonRoleForArtist(nameOriginal, artistGroup);
        if (commonRole) {
          roleControl.patchValue(commonRole);
        }
      }
    }
  }

  private getMostCommonRoleForArtist(
    nameOriginal: string,
    excludeGroup?: FormGroup,
  ): string | null {
    const targetLower = nameOriginal.trim().toLowerCase();
    const roleCounts = new Map<string, number>();

    this.discs.controls.forEach((discControl) => {
      const tracks = discControl.get('tracks') as FormArray;
      if (!tracks) return;
      tracks.controls.forEach((trackControl) => {
        const artists = trackControl.get('artists') as FormArray;
        if (!artists) return;
        artists.controls.forEach((artControl) => {
          if (excludeGroup && artControl === excludeGroup) return;
          const name = artControl.get('name_original')?.value?.trim();
          if (name && name.toLowerCase() === targetLower) {
            const role = artControl.get('role')?.value;
            if (role) {
              roleCounts.set(role, (roleCounts.get(role) ?? 0) + 1);
            }
          }
        });
      });
    });

    if (roleCounts.size === 0) return null;

    let mostCommon: string | null = null;
    let maxCount = 0;
    roleCounts.forEach((count, role) => {
      if (count > maxCount) {
        maxCount = count;
        mostCommon = role;
      }
    });
    return mostCommon;
  }

  protected syncArtistAliases(dIdx: number, tIdx: number, taIdx: number, aliases: string[]): void {
    const artistGroup = this.getTrackArtists(dIdx, tIdx).at(taIdx) as FormGroup;
    const nameOriginal = artistGroup.get('name_original')?.value?.trim();
    if (nameOriginal) {
      this.propagateArtistAliases(nameOriginal, aliases);
    }
  }

  private propagateArtistAliases(nameOriginal: string, aliases: string[]): void {
    const targetLower = nameOriginal.trim().toLowerCase();
    this.discs.controls.forEach((discControl) => {
      const tracks = discControl.get('tracks') as FormArray;
      if (!tracks) return;
      tracks.controls.forEach((trackControl) => {
        const artists = trackControl.get('artists') as FormArray;
        if (!artists) return;
        artists.controls.forEach((artControl) => {
          const name = artControl.get('name_original')?.value?.trim();
          if (name && name.toLowerCase() === targetLower) {
            const currentAliases = artControl.get('aliases')?.value;
            if (JSON.stringify(currentAliases) !== JSON.stringify(aliases)) {
              artControl.patchValue({ aliases }, { emitEvent: false });
            }
          }
        });
      });
    });
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
}
