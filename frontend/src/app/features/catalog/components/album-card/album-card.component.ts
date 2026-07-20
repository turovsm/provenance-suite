import { Component, input, output } from '@angular/core';
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

  protected handleDelete(event: MouseEvent): void {
    event.stopPropagation();
    if (confirm(`Remove "${this.album().title_original}" from archive?`)) {
      this.deleteRequested.emit(this.album().id);
    }
  }
}
