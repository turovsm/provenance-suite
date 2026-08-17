import { Component, computed, input, output } from '@angular/core';
import { EntitySummary } from '../../../../domain/models/music.model';
import { stripMarkdown } from '../../../../shared/utils/markdown-cleaner';

@Component({
  selector: 'app-entity-card',
  standalone: true,
  styleUrls: ['./entity-card.component.css'],
  templateUrl: './entity-card.component.html',
})
export class EntityCardComponent {
  readonly entity = input.required<EntitySummary>();
  readonly isSuperuser = input<boolean>(false);
  readonly isLoadingEdit = input<boolean>(false);

  readonly cardClicked = output<EntitySummary>();
  readonly editRequested = output<EntitySummary>();
  readonly deleteRequested = output<EntitySummary>();

  protected hasImageError = false;

  protected readonly cleanDescription = computed(() => {
    return stripMarkdown(this.entity().description);
  });

  protected onImageError(): void {
    this.hasImageError = true;
  }

  protected getFallbackIcon(): string {
    switch (this.entity().entity_type) {
      case 'artist':
        return 'person';
      case 'franchise':
        return 'sports_esports';
      case 'label':
        return 'album';
      case 'publisher':
        return 'domain';
      default:
        return 'folder_shared';
    }
  }

  protected handleCardClick(): void {
    if (this.isLoadingEdit()) return;
    this.cardClicked.emit(this.entity());
  }

  protected handleEdit(event: MouseEvent): void {
    event.stopPropagation();
    event.preventDefault();
    if (this.isLoadingEdit()) return;
    this.editRequested.emit(this.entity());
  }

  protected handleDelete(event: MouseEvent): void {
    event.stopPropagation();
    event.preventDefault();
    if (this.isLoadingEdit()) return;
    if (confirm(`Remove "${this.entity().name_original}" from master registry?`)) {
      this.deleteRequested.emit(this.entity());
    }
  }
}
