import { Injectable, computed, inject, signal } from '@angular/core';
import { catchError, of } from 'rxjs';
import { ALBUM_REPOSITORY_PORT } from '../../../core/tokens/album.token';
import {
  AlbumIngestRequest,
  AlbumSummary,
  LibraryCategory,
} from '../../../domain/models/music.model';

@Injectable({
  providedIn: 'root',
})
export class AlbumStateEngine {
  private readonly repo = inject(ALBUM_REPOSITORY_PORT);

  // Private write signals
  private readonly albumsSignal = signal<AlbumSummary[]>([]);
  private readonly totalCountSignal = signal<number>(0);
  private readonly loadingSignal = signal<boolean>(false);
  private readonly submittingSignal = signal<boolean>(false);
  private readonly errorSignal = signal<string | null>(null);

  // Filtering & Pagination state signals
  private readonly activeCategorySignal = signal<LibraryCategory | null>(null);
  private readonly searchQuerySignal = signal<string>('');
  private readonly pageSignal = signal<number>(1);
  private readonly pageSizeSignal = signal<number>(24);

  // Public read-only computed projections
  readonly albums = computed(() => this.albumsSignal());
  readonly totalCount = computed(() => this.totalCountSignal());
  readonly isLoading = computed(() => this.loadingSignal());
  readonly isSubmitting = computed(() => this.submittingSignal());
  readonly error = computed(() => this.errorSignal());
  readonly activeCategory = computed(() => this.activeCategorySignal());
  readonly searchQuery = computed(() => this.searchQuerySignal());
  readonly currentPage = computed(() => this.pageSignal());
  readonly pageSize = computed(() => this.pageSizeSignal());

  readonly totalPages = computed(
    () => Math.ceil(this.totalCountSignal() / this.pageSizeSignal()) || 1,
  );

  readonly hasAlbums = computed(() => this.albumsSignal().length > 0);

  setCategory(category: LibraryCategory | null): void {
    this.activeCategorySignal.set(category);
    this.pageSignal.set(1);
    this.queryCatalog();
  }

  setSearchQuery(query: string): void {
    this.searchQuerySignal.set(query);
    this.pageSignal.set(1);
    this.queryCatalog();
  }

  setPage(page: number): void {
    if (page < 1 || page > this.totalPages()) return;
    this.pageSignal.set(page);
    this.queryCatalog();
  }

  queryCatalog(): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);

    const limit = this.pageSizeSignal();
    const offset = (this.pageSignal() - 1) * limit;

    this.repo
      .fetchAlbums(this.activeCategorySignal(), this.searchQuerySignal(), limit, offset)
      .pipe(
        catchError((err) => {
          const msg = err.error?.detail || 'Failed to fetch catalog items.';
          this.errorSignal.set(msg);
          this.loadingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (!res) return;
        this.albumsSignal.set(res.items);
        this.totalCountSignal.set(res.total_count);
        this.loadingSignal.set(false);
      });
  }

  ingestAlbum(payload: AlbumIngestRequest, onSuccess?: () => void): void {
    this.submittingSignal.set(true);
    this.errorSignal.set(null);

    this.repo
      .ingestAlbum(payload)
      .pipe(
        catchError((err) => {
          const msg = err.error?.detail || 'Failed to add album entry.';
          this.errorSignal.set(msg);
          this.submittingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (!res) return;
        this.submittingSignal.set(false);
        this.queryCatalog();
        if (onSuccess) onSuccess();
      });
  }

  deleteAlbum(albumId: string): void {
    this.repo
      .deleteAlbum(albumId)
      .pipe(
        catchError((err) => {
          const msg = err.error?.detail || 'Deletion failed.';
          this.errorSignal.set(msg);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (res === null && this.errorSignal()) return;
        this.queryCatalog();
      });
  }
}
