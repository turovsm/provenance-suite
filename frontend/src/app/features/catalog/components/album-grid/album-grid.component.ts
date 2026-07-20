import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { AuthStateEngine } from '../../../auth/state/auth.state';
import { AlbumStateEngine } from '../../state/album.state';
import { AlbumCardComponent } from '../album-card/album-card.component';
import { LibraryCategory } from '../../../../domain/models/music.model';

@Component({
  selector: 'app-album-grid',
  standalone: true,
  imports: [AlbumCardComponent],
  styleUrls: ['./album-grid.component.css'],
  templateUrl: './album-grid.component.html',
})
export class AlbumGridComponent implements OnInit, OnDestroy {
  protected readonly state = inject(AlbumStateEngine);
  protected readonly authState = inject(AuthStateEngine);
  private readonly route = inject(ActivatedRoute);

  // RxJS pipeline for 300ms search input debouncing
  private readonly searchInput$ = new Subject<string>();
  private searchSubscription?: Subscription;

  ngOnInit(): void {
    // 300ms Debounce pipeline prevents excessive API queries during rapid typing
    this.searchSubscription = this.searchInput$
      .pipe(debounceTime(300), distinctUntilChanged())
      .subscribe((term) => {
        this.state.setSearchQuery(term);
      });

    // React to route parameter changes
    this.route.params.subscribe((params) => {
      const categoryParam = params['category'] as string | undefined;

      if (!categoryParam || categoryParam.toLowerCase() === 'all') {
        this.state.setCategory(null);
      } else {
        this.state.setCategory(categoryParam as LibraryCategory);
      }
    });
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

  protected handleDeleteAlbum(albumId: string): void {
    this.state.deleteAlbum(albumId);
  }
}
