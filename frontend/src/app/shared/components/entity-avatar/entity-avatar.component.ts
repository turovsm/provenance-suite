import { NgOptimizedImage } from '@angular/common';
import { Component, computed, effect, input, signal, untracked } from '@angular/core';

export type EntityAvatarSize = 'sm' | 'md' | 'lg';

const SIZE_DIMENSION_MAP: Record<EntityAvatarSize, number> = {
  sm: 54,
  md: 64,
  lg: 140,
};

@Component({
  selector: 'app-entity-avatar',
  standalone: true,
  imports: [NgOptimizedImage],
  styleUrls: ['./entity-avatar.component.css'],
  templateUrl: './entity-avatar.component.html',
})
export class EntityAvatarComponent {
  readonly imageUrl = input<string | null | undefined>(null);
  readonly name = input<string>('');
  readonly entityType = input<string>('artist');
  readonly size = input<EntityAvatarSize>('md');

  protected readonly hasImageError = signal<boolean>(false);

  constructor() {
    effect(() => {
      this.imageUrl();
      untracked(() => {
        this.hasImageError.set(false);
      });
    });
  }

  protected readonly isArtist = computed(() => this.entityType() === 'artist');

  protected readonly dimension = computed(() => SIZE_DIMENSION_MAP[this.size()]);

  protected readonly fallbackIcon = computed(() => {
    switch (this.entityType()) {
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
  });

  protected onImageError(): void {
    this.hasImageError.set(true);
  }
}
