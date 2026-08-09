import { Injectable, inject } from '@angular/core';
import { Observable, map, of } from 'rxjs';
import { ALBUM_REPOSITORY_PORT } from '../../core/tokens/album.token';
import { MasterArtist, MasterEvent, MasterFranchise } from '../../domain/models/music.model';
import { AutocompleteOption, EntityType } from '../models/autocomplete.model';

function artistToOption(a: MasterArtist): AutocompleteOption {
  return { id: a.id, display: a.name_original, subValue: a.aliases?.[0] || undefined, raw: a };
}

function eventToOption(e: MasterEvent): AutocompleteOption {
  return { id: e.id, display: e.short_name, subValue: e.full_name || undefined, raw: e };
}

function franchiseToOption(f: MasterFranchise): AutocompleteOption {
  return { id: f.id, display: f.name_original, subValue: f.aliases?.[0] || undefined, raw: f };
}

@Injectable({ providedIn: 'root' })
export class EntitySearchService {
  private readonly repo = inject(ALBUM_REPOSITORY_PORT);

  search(entityType: EntityType, query: string): Observable<AutocompleteOption[]> {
    switch (entityType) {
      case 'artist':
        return this.repo.searchArtists(query).pipe(map((list) => list.map(artistToOption)));
      case 'event':
        return this.repo.searchEvents(query).pipe(map((list) => list.map(eventToOption)));
      case 'franchise':
        return this.repo.searchFranchises(query).pipe(map((list) => list.map(franchiseToOption)));
      case 'label':
        return this.repo
          .getLabels(query)
          .pipe(map((list) => list.map((str) => ({ display: str, raw: str }))));
      case 'publisher':
        return this.repo
          .getPublishers(query)
          .pipe(map((list) => list.map((str) => ({ display: str, raw: str }))));
      default:
        return of([]);
    }
  }

  create(entityType: EntityType, name: string): Observable<AutocompleteOption | null> {
    switch (entityType) {
      case 'artist':
        return this.repo.createArtist(name).pipe(map(artistToOption));
      case 'event':
        return this.repo.createEvent(name).pipe(map(eventToOption));
      case 'franchise':
        return this.repo.createFranchise(name).pipe(map(franchiseToOption));
      default:
        return of(null);
    }
  }

  resolveById(entityType: EntityType, uuid: string): Observable<AutocompleteOption | null> {
    return this.search(entityType, uuid).pipe(
      map((options) => options.find((o) => o.id === uuid) ?? null),
    );
  }
}
