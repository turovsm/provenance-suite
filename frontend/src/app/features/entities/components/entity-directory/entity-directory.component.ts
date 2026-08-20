import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { EntitySummary } from '../../../../domain/models/music.model';
import { SelectOption } from '../../../../shared/components/custom-select/custom-select.component';
import { PaginationBarComponent } from '../../../../shared/components/pagination-bar/pagination-bar.component';
import { SearchInputComponent } from '../../../../shared/components/search-input/search-input.component';
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

const PAGE_SIZE_OPTIONS: SelectOption[] = [
  { label: '24 / page', value: '24' },
  { label: '48 / page', value: '48' },
  { label: '96 / page', value: '96' },
];

@Component({
  selector: 'app-entity-directory',
  standalone: true,
  imports: [
    EntityCardComponent,
    EntityFormModalComponent,
    PaginationBarComponent,
    SearchInputComponent,
  ],
  styleUrls: ['./entity-directory.component.css'],
  templateUrl: './entity-directory.component.html',
})
export class EntityDirectoryComponent implements OnInit {
  protected readonly state = inject(EntityStateEngine);
  protected readonly authState = inject(AuthStateEngine);
  private readonly router = inject(Router);

  protected readonly typeTabs = TYPE_TABS;
  protected readonly pageSizeOptions = PAGE_SIZE_OPTIONS;
  protected isAddModalOpen = false;
  protected readonly entityToEdit = signal<EntitySummary | null>(null);

  ngOnInit(): void {
    this.state.queryDirectory();
  }

  protected handleSearchChange(term: string): void {
    this.state.setSearchQuery(term);
  }

  protected handleTypeChange(type: string): void {
    this.state.setActiveType(type);
  }

  protected handlePageChange(newPage: number): void {
    this.state.setPage(newPage);
  }

  protected handlePageSizeChange(size: number): void {
    this.state.setPageSize(size);
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
