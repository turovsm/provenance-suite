import { Component, Input } from '@angular/core';
import { FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MasterArtist } from '../../../../../domain/models/music.model';
import { AliasesChipInputComponent } from '../../../../../shared/components/aliases-chip-input/aliases-chip-input.component';
import { EntityAutocompleteComponent } from '../../../../../shared/components/entity-autocomplete/entity-autocomplete.component';
import { AutocompleteOption } from '../../../../../shared/models/autocomplete.model';

@Component({
  selector: 'app-basic-info-tab',
  standalone: true,
  imports: [ReactiveFormsModule, EntityAutocompleteComponent, AliasesChipInputComponent],
  styleUrls: ['../album-form-modal.component.css'],
  templateUrl: './basic-info-tab.component.html',
})
export class BasicInfoTabComponent {
  @Input({ required: true }) form!: FormGroup;

  protected handleAlbumArtistSelected(option: AutocompleteOption): void {
    const raw = option.raw as MasterArtist;
    if (raw && Array.isArray(raw.aliases) && raw.aliases.length > 0) {
      const currentAliases = this.form.get('aliases')?.value;
      if (!currentAliases || currentAliases.length === 0) {
        this.form.patchValue({ aliases: raw.aliases });
      }
    }
  }
}
