import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { EntitySummary, EntityTypeTag } from '../../../../domain/models/music.model';
import { AuthStateEngine } from '../../../auth/state/auth.state';
import { AlbumCardComponent } from '../../../catalog/components/album-card/album-card.component';
import { AlbumDetailDrawerComponent } from '../../../catalog/components/album-detail-drawer/album-detail-drawer.component';
import { AlbumStateEngine } from '../../../catalog/state/album.state';
import { EntityStateEngine } from '../../state/entity.state';
import { EntityFormModalComponent } from '../entity-form-modal/entity-form-modal.component';

@Component({
  selector: 'app-entity-detail',
  standalone: true,
  imports: [AlbumCardComponent, AlbumDetailDrawerComponent, EntityFormModalComponent],
  styleUrls: ['./entity-detail.component.css'],
  templateUrl: './entity-detail.component.html',
})
export class EntityDetailComponent implements OnInit, OnDestroy {
  protected readonly state = inject(EntityStateEngine);
  protected readonly albumState = inject(AlbumStateEngine);
  protected readonly authState = inject(AuthStateEngine);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  protected entityType = signal<string>('artist');
  protected entityId = signal<string>('');
  protected isEditModalOpen = false;

  readonly currentEntity = computed(() => {
    const type = this.entityType();
    if (type === 'artist') {
      const d = this.state.activeArtistDetail();
      return d
        ? {
            id: d.id,
            type: 'artist' as EntityTypeTag,
            name_original: d.name_original,
            aliases: d.aliases,
            image_url: d.image_url,
            description: d.description,
            franchise_type: null,
          }
        : null;
    }
    if (type === 'franchise') {
      const d = this.state.activeFranchiseDetail();
      return d
        ? {
            id: d.id,
            type: 'franchise' as EntityTypeTag,
            name_original: d.name_original,
            aliases: d.aliases,
            image_url: d.image_url,
            description: d.description,
            franchise_type: d.franchise_type,
          }
        : null;
    }
    if (type === 'label') {
      const d = this.state.activeLabelDetail();
      return d
        ? {
            id: d.id,
            type: 'label' as EntityTypeTag,
            name_original: d.name_original,
            aliases: d.aliases,
            image_url: d.image_url,
            description: d.description,
            franchise_type: null,
          }
        : null;
    }
    if (type === 'publisher') {
      const d = this.state.activePublisherDetail();
      return d
        ? {
            id: d.id,
            type: 'publisher' as EntityTypeTag,
            name_original: d.name_original,
            aliases: d.aliases,
            image_url: d.image_url,
            description: d.description,
            franchise_type: null,
          }
        : null;
    }
    return null;
  });

  readonly summaryForModal = computed<EntitySummary | null>(() => {
    const curr = this.currentEntity();
    if (!curr) return null;
    return {
      id: curr.id,
      name_original: curr.name_original,
      aliases: curr.aliases,
      entity_type: curr.type,
      image_url: curr.image_url,
      description: curr.description,
      franchise_type: curr.franchise_type,
    };
  });

  ngOnInit(): void {
    this.route.params.subscribe((params) => {
      const type = params['type'];
      const id = params['id'];
      if (type && id) {
        this.entityType.set(type);
        this.entityId.set(id);
        this.state.loadEntityDetail(type, id);
      }
    });
  }

  ngOnDestroy(): void {
    this.state.clearDetailState();
  }

  protected getFallbackIcon(type: string): string {
    switch (type) {
      case 'artist':
        return 'person';
      case 'franchise':
        return 'sports_esports';
      case 'label':
        return 'album';
      case 'publisher':
        return 'domain';
      default:
        return 'folder_shared';
    }
  }

  protected goBack(): void {
    void this.router.navigate(['/entities']);
  }

  protected handleSelectAlbum(albumId: string): void {
    this.albumState.selectAlbum(albumId);
  }

  protected openEditModal(): void {
    this.isEditModalOpen = true;
  }

  protected handleDelete(): void {
    const curr = this.currentEntity();
    if (!curr) return;
    if (confirm(`Delete master entity "${curr.name_original}"?`)) {
      if (curr.type === 'artist') {
        this.state.deleteArtist(curr.id, () => this.goBack());
      } else if (curr.type === 'franchise') {
        this.state.deleteFranchise(curr.id, () => this.goBack());
      } else if (curr.type === 'label') {
        this.state.deleteLabel(curr.id, () => this.goBack());
      } else if (curr.type === 'publisher') {
        this.state.deletePublisher(curr.id, () => this.goBack());
      }
    }
  }
}
