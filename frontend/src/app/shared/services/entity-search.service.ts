import { Injectable, inject } from '@angular/core';
import { Observable, catchError, map, of, tap } from 'rxjs';
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
  private readonly optionCache = new Map<string, AutocompleteOption>();

  public cacheOption(entityType: EntityType, option: AutocompleteOption): void {
    if (option && option.id) {
      this.optionCache.set(`${entityType}:${option.id}`, option);
    }
  }

  search(entityType: EntityType, query: string): Observable<AutocompleteOption[]> {
    let search$: Observable<AutocompleteOption[]>;
    switch (entityType) {
      case 'artist':
        search$ = this.repo.searchArtists(query).pipe(map((list) => list.map(artistToOption)));
        break;
      case 'event':
        search$ = this.repo.searchEvents(query).pipe(map((list) => list.map(eventToOption)));
        break;
      case 'franchise':
        search$ = this.repo
          .searchFranchises(query)
          .pipe(map((list) => list.map(franchiseToOption)));
        break;
      case 'label':
        search$ = this.repo
          .getLabels(query)
          .pipe(map((list) => list.map((str) => ({ display: str, raw: str }))));
        break;
      case 'publisher':
        search$ = this.repo
          .getPublishers(query)
          .pipe(map((list) => list.map((str) => ({ display: str, raw: str }))));
        break;
      default:
        return of([]);
    }

    return search$.pipe(
      tap((options) => {
        options.forEach((opt) => this.cacheOption(entityType, opt));
      }),
    );
  }

  create(entityType: EntityType, name: string): Observable<AutocompleteOption | null> {
    let create$: Observable<AutocompleteOption | null>;
    switch (entityType) {
      case 'artist':
        create$ = this.repo.createArtist(name).pipe(map(artistToOption));
        break;
      case 'event':
        create$ = this.repo.createEvent(name).pipe(map(eventToOption));
        break;
      case 'franchise':
        create$ = this.repo.createFranchise(name).pipe(map(franchiseToOption));
        break;
      default:
        return of(null);
    }

    return create$.pipe(
      tap((created) => {
        if (created) {
          this.cacheOption(entityType, created);
        }
      }),
    );
  }

  resolveById(entityType: EntityType, uuid: string): Observable<AutocompleteOption | null> {
    const cacheKey = `${entityType}:${uuid}`;
    if (this.optionCache.has(cacheKey)) {
      return of(this.optionCache.get(cacheKey)!);
    }

    if (entityType === 'event') {
      return this.repo.getEventDetail(uuid).pipe(
        map((ev) => {
          if (!ev) return null;
          const opt = eventToOption(ev);
          this.cacheOption(entityType, opt);
          return opt;
        }),
        catchError(() => of(null)),
      );
    }

    return this.search(entityType, '').pipe(
      map(() => this.optionCache.get(cacheKey) ?? null),
      catchError(() => of(null)),
    );
  }
}
