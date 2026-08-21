import { NgOptimizedImage } from '@angular/common';
import { Component, computed, effect, input, output, signal, untracked } from '@angular/core';
import { AlbumSummary } from '../../../../domain/models/music.model';
import { CardActionsComponent } from '../../../../shared/components/card-actions/card-actions.component';

@Component({
  selector: 'app-album-card',
  standalone: true,
  imports: [CardActionsComponent, NgOptimizedImage],
  styleUrls: ['./album-card.component.css'],
  templateUrl: './album-card.component.html',
})
export class AlbumCardComponent {
  readonly album = input.required<AlbumSummary>();
  readonly isAdmin = input<boolean>(false);
  readonly isLoadingEdit = input<boolean>(false);

  readonly deleteRequested = output<string>();
  readonly editRequested = output<string>();
  readonly cardClicked = output<string>();

  protected readonly hasImageError = signal<boolean>(false);

  constructor() {
    effect(() => {
      this.coverUrl();
      untracked(() => {
        this.hasImageError.set(false);
      });
    });
  }

  protected readonly coverUrl = computed(() => {
    const covers = this.album().covers;
    if (!covers || covers.length === 0) return null;
    const front = covers.find((c) => c.cover_type.toLowerCase() === 'front');
    return front ? front.url : covers[0].url;
  });

  protected readonly formattedReleaseDate = computed(() => {
    const { release_year, release_month, release_day } = this.album();
    if (!release_year) return null;
    const y = release_year.toString();
    const m = release_month ? release_month.toString().padStart(2, '0') : null;
    const d = release_day ? release_day.toString().padStart(2, '0') : null;
    if (m && d) return `${y}/${m}/${d}`;
    if (m) return `${y}/${m}`;
    return y;
  });

  protected readonly artistName = computed(() => {
    return this.album().album_artist?.name_original || 'Unknown Artist / Circle';
  });

  protected onImageError(): void {
    this.hasImageError.set(true);
  }

  protected handleCardClick(): void {
    if (this.isLoadingEdit()) return;
    this.cardClicked.emit(this.album().id);
  }

  protected handleEdit(): void {
    if (this.isLoadingEdit()) return;
    this.editRequested.emit(this.album().id);
  }

  protected handleDelete(): void {
    if (this.isLoadingEdit()) return;
    if (confirm(`Remove "${this.album().title_original}" from archive?`)) {
      this.deleteRequested.emit(this.album().id);
    }
  }
}
