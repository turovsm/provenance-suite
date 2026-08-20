import { Component, computed, input, output } from '@angular/core';
import { EntitySummary } from '../../../../domain/models/music.model';
import { EntityAvatarComponent } from '../../../../shared/components/entity-avatar/entity-avatar.component';
import { stripMarkdown } from '../../../../shared/utils/markdown-cleaner';

@Component({
  selector: 'app-entity-card',
  standalone: true,
  imports: [EntityAvatarComponent],
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

  protected readonly cleanDescription = computed(() => {
    return stripMarkdown(this.entity().description);
  });

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
