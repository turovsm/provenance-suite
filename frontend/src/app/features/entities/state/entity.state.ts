import { Injectable, computed, inject, signal } from '@angular/core';
import { catchError, of } from 'rxjs';
import { ALBUM_REPOSITORY_PORT } from '../../../core/tokens/album.token';
import {
  AlbumSummary,
  ArtistCreatePayload,
  ArtistDiscography,
  ArtistUpdatePayload,
  EntitySummary,
  FranchiseCreatePayload,
  FranchiseUpdatePayload,
  LabelCreatePayload,
  LabelUpdatePayload,
  MasterArtist,
  MasterFranchise,
  MasterLabel,
  MasterPublisher,
  PublisherCreatePayload,
  PublisherUpdatePayload,
} from '../../../domain/models/music.model';
import { extractErrorMessage } from '../../../shared/utils/error-extractor';

@Injectable({
  providedIn: 'root',
})
export class EntityStateEngine {
  private readonly repo = inject(ALBUM_REPOSITORY_PORT);

  private readonly entitiesSignal = signal<EntitySummary[]>([]);
  private readonly totalCountSignal = signal<number>(0);
  private readonly loadingSignal = signal<boolean>(false);
  private readonly submittingSignal = signal<boolean>(false);
  private readonly errorSignal = signal<string | null>(null);

  private readonly activeTypeSignal = signal<string>('all');
  private readonly searchQuerySignal = signal<string>('');
  private readonly pageSignal = signal<number>(1);
  private readonly pageSizeSignal = signal<number>(24);

  private readonly activeArtistDetailSignal = signal<MasterArtist | null>(null);
  private readonly activeFranchiseDetailSignal = signal<MasterFranchise | null>(null);
  private readonly activeLabelDetailSignal = signal<MasterLabel | null>(null);
  private readonly activePublisherDetailSignal = signal<MasterPublisher | null>(null);
  private readonly artistDiscographySignal = signal<ArtistDiscography | null>(null);
  private readonly entityAlbumsSignal = signal<AlbumSummary[]>([]);

  readonly entities = computed(() => this.entitiesSignal());
  readonly totalCount = computed(() => this.totalCountSignal());
  readonly isLoading = computed(() => this.loadingSignal());
  readonly isSubmitting = computed(() => this.submittingSignal());
  readonly error = computed(() => this.errorSignal());
  readonly activeType = computed(() => this.activeTypeSignal());
  readonly searchQuery = computed(() => this.searchQuerySignal());
  readonly currentPage = computed(() => this.pageSignal());
  readonly pageSize = computed(() => this.pageSizeSignal());

  readonly totalPages = computed(
    () => Math.ceil(this.totalCountSignal() / this.pageSizeSignal()) || 1,
  );
  readonly hasEntities = computed(() => this.entitiesSignal().length > 0);

  readonly activeArtistDetail = computed(() => this.activeArtistDetailSignal());
  readonly activeFranchiseDetail = computed(() => this.activeFranchiseDetailSignal());
  readonly activeLabelDetail = computed(() => this.activeLabelDetailSignal());
  readonly activePublisherDetail = computed(() => this.activePublisherDetailSignal());
  readonly artistDiscography = computed(() => this.artistDiscographySignal());
  readonly entityAlbums = computed(() => this.entityAlbumsSignal());

  setActiveType(type: string): void {
    this.activeTypeSignal.set(type);
    this.pageSignal.set(1);
    this.queryDirectory();
  }

  setSearchQuery(query: string): void {
    this.searchQuerySignal.set(query);
    this.pageSignal.set(1);
    this.queryDirectory();
  }

  setPage(page: number): void {
    if (page < 1 || page > this.totalPages()) return;
    this.pageSignal.set(page);
    this.queryDirectory();
  }

  queryDirectory(): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);

    const limit = this.pageSizeSignal();
    const offset = (this.pageSignal() - 1) * limit;

    this.repo
      .fetchEntities(this.activeTypeSignal(), this.searchQuerySignal(), limit, offset)
      .pipe(
        catchError((err) => {
          const msg = extractErrorMessage(err, 'Failed to query master entity directory.');
          this.errorSignal.set(msg);
          this.loadingSignal.set(false);
          return of({ items: [], total_count: 0, limit, offset });
        }),
      )
      .subscribe((res) => {
        this.entitiesSignal.set(res.items);
        this.totalCountSignal.set(res.total_count);
        this.loadingSignal.set(false);
      });
  }

  loadEntityDetail(type: string, id: string): void {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);
    this.clearDetailState();

    if (type === 'artist') {
      this.repo
        .getArtistDetail(id)
        .pipe(
          catchError((err) => {
            this.errorSignal.set(extractErrorMessage(err, 'Artist detail load failed.'));
            this.loadingSignal.set(false);
            return of(null);
          }),
        )
        .subscribe((artist) => {
          if (artist) {
            this.activeArtistDetailSignal.set(artist);
            this.loadArtistDiscography(id);
          }
        });
    } else if (type === 'franchise') {
      this.repo
        .getFranchiseDetail(id)
        .pipe(
          catchError((err) => {
            this.errorSignal.set(extractErrorMessage(err, 'Franchise detail load failed.'));
            this.loadingSignal.set(false);
            return of(null);
          }),
        )
        .subscribe((franchise) => {
          if (franchise) {
            this.activeFranchiseDetailSignal.set(franchise);
            this.loadFranchiseAlbums(id);
          }
        });
    } else if (type === 'label') {
      this.repo
        .getLabelDetail(id)
        .pipe(
          catchError((err) => {
            this.errorSignal.set(extractErrorMessage(err, 'Label detail load failed.'));
            this.loadingSignal.set(false);
            return of(null);
          }),
        )
        .subscribe((label) => {
          if (label) {
            this.activeLabelDetailSignal.set(label);
            this.loadLabelAlbums(id);
          }
        });
    } else if (type === 'publisher') {
      this.repo
        .getPublisherDetail(id)
        .pipe(
          catchError((err) => {
            this.errorSignal.set(extractErrorMessage(err, 'Publisher detail load failed.'));
            this.loadingSignal.set(false);
            return of(null);
          }),
        )
        .subscribe((pub) => {
          if (pub) {
            this.activePublisherDetailSignal.set(pub);
            this.loadPublisherAlbums(id);
          }
        });
    }
  }

  private loadArtistDiscography(artistId: string): void {
    this.repo
      .getArtistDiscography(artistId)
      .pipe(catchError(() => of(null)))
      .subscribe((disco) => {
        if (disco) this.artistDiscographySignal.set(disco);
        this.loadingSignal.set(false);
      });
  }

  private loadFranchiseAlbums(franchiseId: string): void {
    this.repo
      .getFranchiseAlbums(franchiseId)
      .pipe(catchError(() => of([])))
      .subscribe((albums) => {
        this.entityAlbumsSignal.set(albums);
        this.loadingSignal.set(false);
      });
  }

  private loadLabelAlbums(labelId: string): void {
    this.repo
      .getLabelAlbums(labelId)
      .pipe(catchError(() => of([])))
      .subscribe((albums) => {
        this.entityAlbumsSignal.set(albums);
        this.loadingSignal.set(false);
      });
  }

  private loadPublisherAlbums(publisherId: string): void {
    this.repo
      .getPublisherAlbums(publisherId)
      .pipe(catchError(() => of([])))
      .subscribe((albums) => {
        this.entityAlbumsSignal.set(albums);
        this.loadingSignal.set(false);
      });
  }

  createArtist(payload: ArtistCreatePayload, onSuccess?: () => void): void {
    this.submittingSignal.set(true);
    this.repo
      .createArtistFull(payload)
      .pipe(
        catchError((err) => {
          this.errorSignal.set(extractErrorMessage(err, 'Artist creation failed.'));
          this.submittingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (!res) return;
        this.submittingSignal.set(false);
        this.queryDirectory();
        if (onSuccess) onSuccess();
      });
  }

  updateArtist(id: string, payload: ArtistUpdatePayload, onSuccess?: () => void): void {
    this.submittingSignal.set(true);
    this.repo
      .updateArtist(id, payload)
      .pipe(
        catchError((err) => {
          this.errorSignal.set(extractErrorMessage(err, 'Artist update failed.'));
          this.submittingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (!res) return;
        this.submittingSignal.set(false);
        this.loadEntityDetail('artist', id);
        this.queryDirectory();
        if (onSuccess) onSuccess();
      });
  }

  deleteArtist(id: string, onSuccess?: () => void): void {
    this.repo
      .deleteArtist(id)
      .pipe(catchError(() => of(null)))
      .subscribe(() => {
        this.queryDirectory();
        if (onSuccess) onSuccess();
      });
  }

  createFranchise(payload: FranchiseCreatePayload, onSuccess?: () => void): void {
    this.submittingSignal.set(true);
    this.repo
      .createFranchiseFull(payload)
      .pipe(
        catchError((err) => {
          this.errorSignal.set(extractErrorMessage(err, 'Franchise creation failed.'));
          this.submittingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (!res) return;
        this.submittingSignal.set(false);
        this.queryDirectory();
        if (onSuccess) onSuccess();
      });
  }

  updateFranchise(id: string, payload: FranchiseUpdatePayload, onSuccess?: () => void): void {
    this.submittingSignal.set(true);
    this.repo
      .updateFranchise(id, payload)
      .pipe(
        catchError((err) => {
          this.errorSignal.set(extractErrorMessage(err, 'Franchise update failed.'));
          this.submittingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (!res) return;
        this.submittingSignal.set(false);
        this.loadEntityDetail('franchise', id);
        this.queryDirectory();
        if (onSuccess) onSuccess();
      });
  }

  deleteFranchise(id: string, onSuccess?: () => void): void {
    this.repo
      .deleteFranchise(id)
      .pipe(catchError(() => of(null)))
      .subscribe(() => {
        this.queryDirectory();
        if (onSuccess) onSuccess();
      });
  }

  createLabel(payload: LabelCreatePayload, onSuccess?: () => void): void {
    this.submittingSignal.set(true);
    this.repo
      .createLabel(payload)
      .pipe(
        catchError((err) => {
          this.errorSignal.set(extractErrorMessage(err, 'Label creation failed.'));
          this.submittingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (!res) return;
        this.submittingSignal.set(false);
        this.queryDirectory();
        if (onSuccess) onSuccess();
      });
  }

  updateLabel(id: string, payload: LabelUpdatePayload, onSuccess?: () => void): void {
    this.submittingSignal.set(true);
    this.repo
      .updateLabel(id, payload)
      .pipe(
        catchError((err) => {
          this.errorSignal.set(extractErrorMessage(err, 'Label update failed.'));
          this.submittingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (!res) return;
        this.submittingSignal.set(false);
        this.loadEntityDetail('label', id);
        this.queryDirectory();
        if (onSuccess) onSuccess();
      });
  }

  deleteLabel(id: string, onSuccess?: () => void): void {
    this.repo
      .deleteLabel(id)
      .pipe(catchError(() => of(null)))
      .subscribe(() => {
        this.queryDirectory();
        if (onSuccess) onSuccess();
      });
  }

  createPublisher(payload: PublisherCreatePayload, onSuccess?: () => void): void {
    this.submittingSignal.set(true);
    this.repo
      .createPublisher(payload)
      .pipe(
        catchError((err) => {
          this.errorSignal.set(extractErrorMessage(err, 'Publisher creation failed.'));
          this.submittingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (!res) return;
        this.submittingSignal.set(false);
        this.queryDirectory();
        if (onSuccess) onSuccess();
      });
  }

  updatePublisher(id: string, payload: PublisherUpdatePayload, onSuccess?: () => void): void {
    this.submittingSignal.set(true);
    this.repo
      .updatePublisher(id, payload)
      .pipe(
        catchError((err) => {
          this.errorSignal.set(extractErrorMessage(err, 'Publisher update failed.'));
          this.submittingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((res) => {
        if (!res) return;
        this.submittingSignal.set(false);
        this.loadEntityDetail('publisher', id);
        this.queryDirectory();
        if (onSuccess) onSuccess();
      });
  }

  deletePublisher(id: string, onSuccess?: () => void): void {
    this.repo
      .deletePublisher(id)
      .pipe(catchError(() => of(null)))
      .subscribe(() => {
        this.queryDirectory();
        if (onSuccess) onSuccess();
      });
  }

  clearDetailState(): void {
    this.activeArtistDetailSignal.set(null);
    this.activeFranchiseDetailSignal.set(null);
    this.activeLabelDetailSignal.set(null);
    this.activePublisherDetailSignal.set(null);
    this.artistDiscographySignal.set(null);
    this.entityAlbumsSignal.set([]);
  }
}
