import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { EntitySummary } from '../../../../domain/models/music.model';
import { AuthStateEngine } from '../../../auth/state/auth.state';
import { EntityStateEngine } from '../../state/entity.state';
import { EntityCardComponent } from '../entity-card/entity-card.component';
import { EntityFormModalComponent } from '../entity-form-modal/entity-form-modal.component';

const TYPE_TABS = [
  { label: 'All Entities', value: 'all' },
  { label: 'Artists & Circles', value: 'artist' },
  { label: 'Franchises', value: 'franchise' },
  { label: 'Labels', value: 'label' },
  { label: 'Publishers', value: 'publisher' },
];

@Component({
  selector: 'app-entity-directory',
  standalone: true,
  imports: [EntityCardComponent, EntityFormModalComponent],
  styleUrls: ['./entity-directory.component.css'],
  templateUrl: './entity-directory.component.html',
})
export class EntityDirectoryComponent implements OnInit, OnDestroy {
  protected readonly state = inject(EntityStateEngine);
  protected readonly authState = inject(AuthStateEngine);
  private readonly router = inject(Router);

  protected readonly typeTabs = TYPE_TABS;
  protected isAddModalOpen = false;
  protected readonly entityToEdit = signal<EntitySummary | null>(null);

  private readonly searchInput$ = new Subject<string>();
  private searchSubscription?: Subscription;

  ngOnInit(): void {
    this.searchSubscription = this.searchInput$
      .pipe(debounceTime(300), distinctUntilChanged())
      .subscribe((term) => {
        this.state.setSearchQuery(term);
      });

    this.state.queryDirectory();
  }

  ngOnDestroy(): void {
    this.searchSubscription?.unsubscribe();
  }

  protected handleSearchInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.searchInput$.next(value);
  }

  protected handleTypeChange(type: string): void {
    this.state.setActiveType(type);
  }

  protected handlePageChange(newPage: number): void {
    this.state.setPage(newPage);
  }

  protected handleSelectEntity(entity: EntitySummary): void {
    void this.router.navigate(['/entities', entity.entity_type, entity.id]);
  }

  protected handleEditEntity(entity: EntitySummary): void {
    this.entityToEdit.set(entity);
    this.isAddModalOpen = true;
  }

  protected handleDeleteEntity(entity: EntitySummary): void {
    if (entity.entity_type === 'artist') {
      this.state.deleteArtist(entity.id);
    } else if (entity.entity_type === 'franchise') {
      this.state.deleteFranchise(entity.id);
    } else if (entity.entity_type === 'label') {
      this.state.deleteLabel(entity.id);
    } else if (entity.entity_type === 'publisher') {
      this.state.deletePublisher(entity.id);
    }
  }

  protected openAddModal(): void {
    this.entityToEdit.set(null);
    this.isAddModalOpen = true;
  }

  protected closeAddModal(): void {
    this.isAddModalOpen = false;
    this.entityToEdit.set(null);
  }
}
