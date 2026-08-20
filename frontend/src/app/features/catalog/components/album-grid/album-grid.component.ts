import { Component, OnInit, inject, signal } from '@angular/core';
import { ALBUM_REPOSITORY_PORT } from '../../../../core/tokens/album.token';
import { AlbumDetailResponse } from '../../../../domain/models/music.model';
import { SelectOption } from '../../../../shared/components/custom-select/custom-select.component';
import { EmptyStateComponent } from '../../../../shared/components/empty-state/empty-state.component';
import { PaginationBarComponent } from '../../../../shared/components/pagination-bar/pagination-bar.component';
import { SearchInputComponent } from '../../../../shared/components/search-input/search-input.component';
import { AuthStateEngine } from '../../../auth/state/auth.state';
import { AlbumStateEngine } from '../../state/album.state';
import { AlbumCardComponent } from '../album-card/album-card.component';
import { AlbumDetailDrawerComponent } from '../album-detail-drawer/album-detail-drawer.component';
import { AlbumFormModalComponent } from '../album-form-modal/album-form-modal.component';

const PAGE_SIZE_OPTIONS: SelectOption[] = [
  { label: '24 / page', value: '24' },
  { label: '48 / page', value: '48' },
  { label: '96 / page', value: '96' },
];

@Component({
  selector: 'app-album-grid',
  standalone: true,
  imports: [
    AlbumCardComponent,
    AlbumFormModalComponent,
    AlbumDetailDrawerComponent,
    PaginationBarComponent,
    SearchInputComponent,
    EmptyStateComponent,
  ],
  styleUrls: ['./album-grid.component.css'],
  templateUrl: './album-grid.component.html',
})
export class AlbumGridComponent implements OnInit {
  protected readonly state = inject(AlbumStateEngine);
  protected readonly authState = inject(AuthStateEngine);
  private readonly repo = inject(ALBUM_REPOSITORY_PORT);

  protected readonly pageSizeOptions = PAGE_SIZE_OPTIONS;
  protected isAddModalOpen = false;
  protected readonly albumToEdit = signal<AlbumDetailResponse | null>(null);
  protected readonly loadingEditId = signal<string | null>(null);

  ngOnInit(): void {
    this.state.queryCatalog();
  }

  protected handleSearchChange(term: string): void {
    this.state.setSearchQuery(term);
  }

  protected handlePageChange(newPage: number): void {
    this.state.setPage(newPage);
  }

  protected handlePageSizeChange(size: number): void {
    this.state.setPageSize(size);
  }

  protected handleSelectAlbum(albumId: string): void {
    this.state.selectAlbum(albumId);
  }

  protected handleEditAlbum(albumId: string): void {
    if (this.loadingEditId()) return;
    this.loadingEditId.set(albumId);

    this.repo.getAlbumDetail(albumId).subscribe({
      next: (detail) => {
        this.loadingEditId.set(null);
        if (detail) {
          this.albumToEdit.set(detail);
          this.isAddModalOpen = true;
        }
      },
      error: () => {
        this.loadingEditId.set(null);
      },
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
