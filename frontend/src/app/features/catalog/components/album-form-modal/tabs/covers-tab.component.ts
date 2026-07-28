import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CustomSelectComponent } from '../../../../../shared/components/custom-select/custom-select.component';
import { formatBytes } from '../../../../../shared/utils/format-bytes';
import { COVER_TYPES } from '../../../constants/album-form-options';
import { CoverListService } from '../../../services/cover-list.service';

@Component({
  selector: 'app-covers-tab',
  standalone: true,
  imports: [FormsModule, CustomSelectComponent],
  styleUrls: ['../album-form-modal.component.css'],
  templateUrl: './covers-tab.component.html',
})
export class CoversTabComponent {
  protected readonly coverService = inject(CoverListService);

  protected readonly coverTypes = COVER_TYPES;
  protected readonly formatBytes = formatBytes;
  protected coverTypeSelected = 'Front';
  protected isDraggingOver = false;

  protected onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDraggingOver = true;
  }

  protected onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDraggingOver = false;
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDraggingOver = false;
    const files = event.dataTransfer?.files;
    if (files?.length) {
      this.coverService.addFiles(files, this.coverTypeSelected || 'Front');
    }
  }

  protected handleCoverSelected(event: Event): void {
    const files = (event.target as HTMLInputElement).files;
    if (files?.length) {
      this.coverService.addFiles(files, this.coverTypeSelected || 'Front');
    }
  }
}
