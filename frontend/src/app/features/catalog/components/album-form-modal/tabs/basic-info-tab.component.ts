import { Component, Input } from '@angular/core';
import { FormGroup, ReactiveFormsModule } from '@angular/forms';
import { EntityAutocompleteComponent } from '../../../../../shared/components/entity-autocomplete/entity-autocomplete.component';

@Component({
  selector: 'app-basic-info-tab',
  standalone: true,
  imports: [ReactiveFormsModule, EntityAutocompleteComponent],
  styleUrls: ['../album-form-modal.component.css'],
  templateUrl: './basic-info-tab.component.html',
})
export class BasicInfoTabComponent {
  @Input({ required: true }) form!: FormGroup;
}
