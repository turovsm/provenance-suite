import { Component, computed, input, output } from '@angular/core';
import { AlbumSummary } from '../../../../domain/models/music.model';

@Component({
  selector: 'app-album-card',
  standalone: true,
  styleUrls: ['./album-card.component.css'],
  templateUrl: './album-card.component.html',
})
export class AlbumCardComponent {
  readonly album = input.required<AlbumSummary>();
  readonly isSuperuser = input<boolean>(false);

  readonly deleteRequested = output<string>();
  readonly editRequested = output<string>();
  readonly cardClicked = output<string>();

  protected hasImageError = false;

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
    if (m && d) return `${y}.${m}.${d}`;
    if (m) return `${y}.${m}`;
    return y;
  });

  protected readonly artistName = computed(() => {
    return this.album().album_artist?.name_original || 'Unknown Artist / Circle';
  });

  protected onImageError(): void {
    this.hasImageError = true;
  }

  protected handleCardClick(): void {
    this.cardClicked.emit(this.album().id);
  }

  protected handleEdit(event: MouseEvent): void {
    event.stopPropagation();
    this.editRequested.emit(this.album().id);
  }

  protected handleDelete(event: MouseEvent): void {
    event.stopPropagation();
    if (confirm(`Remove "${this.album().title_original}" from archive?`)) {
      this.deleteRequested.emit(this.album().id);
    }
  }
}
