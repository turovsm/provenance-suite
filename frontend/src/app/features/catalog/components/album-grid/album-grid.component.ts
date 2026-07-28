import { Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { AuthStateEngine } from '../../../auth/state/auth.state';
import { AlbumStateEngine } from '../../state/album.state';
import { AlbumCardComponent } from '../album-card/album-card.component';
import { AlbumDetailDrawerComponent } from '../album-detail-drawer/album-detail-drawer.component';
import { AlbumFormModalComponent } from '../album-form-modal/album-form-modal.component';
import { AlbumDetailResponse } from '../../../../domain/models/music.model';
import { ALBUM_REPOSITORY_PORT } from '../../../../core/tokens/album.token';

@Component({
  selector: 'app-album-grid',
  standalone: true,
  imports: [AlbumCardComponent, AlbumFormModalComponent, AlbumDetailDrawerComponent],
  styleUrls: ['./album-grid.component.css'],
  templateUrl: './album-grid.component.html',
})
export class AlbumGridComponent implements OnInit, OnDestroy {
  protected readonly state = inject(AlbumStateEngine);
  protected readonly authState = inject(AuthStateEngine);
  private readonly repo = inject(ALBUM_REPOSITORY_PORT);

  protected isAddModalOpen = false;
  protected readonly albumToEdit = signal<AlbumDetailResponse | null>(null);

  private readonly searchInput$ = new Subject<string>();
  private searchSubscription?: Subscription;

  ngOnInit(): void {
    this.searchSubscription = this.searchInput$
      .pipe(debounceTime(300), distinctUntilChanged())
      .subscribe((term) => {
        this.state.setSearchQuery(term);
      });

    this.state.queryCatalog();
  }

  ngOnDestroy(): void {
    this.searchSubscription?.unsubscribe();
  }

  protected handleSearchInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.searchInput$.next(value);
  }

  protected handlePageChange(newPage: number): void {
    this.state.setPage(newPage);
  }

  protected handleSelectAlbum(albumId: string): void {
    this.state.selectAlbum(albumId);
  }

  protected handleEditAlbum(albumId: string): void {
    this.repo.getAlbumDetail(albumId).subscribe((detail) => {
      if (detail) {
        this.albumToEdit.set(detail);
        this.isAddModalOpen = true;
      }
    });
  }

  protected handleDeleteAlbum(albumId: string): void {
    this.state.deleteAlbum(albumId);
  }

  protected openAddModal(): void {
    this.albumToEdit.set(null);
    this.isAddModalOpen = true;
  }

  protected closeAddModal(): void {
    this.isAddModalOpen = false;
    this.albumToEdit.set(null);
  }
}
