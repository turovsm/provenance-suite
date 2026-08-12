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
  private readonly sessionOptionsMap = new Map<EntityType, Map<string, AutocompleteOption>>();

  public cacheOption(entityType: EntityType, option: AutocompleteOption): void {
    if (!option || !option.display || !option.display.trim()) return;

    const cleanDisplay = option.display.trim();
    if (!option.id) {
      option.id = `${entityType}:${cleanDisplay.toLowerCase()}`;
    }

    let typeMap = this.sessionOptionsMap.get(entityType);
    if (!typeMap) {
      typeMap = new Map<string, AutocompleteOption>();
      this.sessionOptionsMap.set(entityType, typeMap);
    }

    typeMap.set(option.id, option);
    typeMap.set(cleanDisplay.toLowerCase(), option);
    this.optionCache.set(`${entityType}:${option.id}`, option);
    this.optionCache.set(`${entityType}:${cleanDisplay.toLowerCase()}`, option);
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
          .pipe(map((list) => list.map((str) => ({ id: `label:${str}`, display: str, raw: str }))));
        break;
      case 'publisher':
        search$ = this.repo
          .getPublishers(query)
          .pipe(
            map((list) => list.map((str) => ({ id: `publisher:${str}`, display: str, raw: str }))),
          );
        break;
      default:
        return of([]);
    }

    return search$.pipe(
      map((remoteOptions) => {
        remoteOptions.forEach((opt) => this.cacheOption(entityType, opt));

        const typeMap = this.sessionOptionsMap.get(entityType);
        if (!typeMap || typeMap.size === 0) {
          return remoteOptions;
        }

        const qLower = query.trim().toLowerCase();
        const merged = [...remoteOptions];
        const seenIds = new Set(remoteOptions.map((o) => o.id).filter(Boolean));
        const seenDisplays = new Set(remoteOptions.map((o) => o.display.toLowerCase()));

        typeMap.forEach((opt) => {
          if (
            (!qLower || opt.display.toLowerCase().includes(qLower)) &&
            (!opt.id || !seenIds.has(opt.id)) &&
            !seenDisplays.has(opt.display.toLowerCase())
          ) {
            if (opt.id) seenIds.add(opt.id);
            seenDisplays.add(opt.display.toLowerCase());
            merged.push(opt);
          }
        });

        return merged;
      }),
      catchError(() => {
        const typeMap = this.sessionOptionsMap.get(entityType);
        if (!typeMap) return of([]);
        const qLower = query.trim().toLowerCase();
        const results: AutocompleteOption[] = [];
        const seenDisplays = new Set<string>();

        typeMap.forEach((opt) => {
          if (
            (!qLower || opt.display.toLowerCase().includes(qLower)) &&
            !seenDisplays.has(opt.display.toLowerCase())
          ) {
            seenDisplays.add(opt.display.toLowerCase());
            results.push(opt);
          }
        });

        return of(results);
      }),
    );
  }

  create(entityType: EntityType, name: string): Observable<AutocompleteOption | null> {
    const cleanName = name.trim();
    if (!cleanName) return of(null);

    let create$: Observable<AutocompleteOption | null>;
    switch (entityType) {
      case 'artist':
        create$ = this.repo.createArtist(cleanName).pipe(map(artistToOption));
        break;
      case 'event':
        create$ = this.repo.createEvent(cleanName).pipe(map(eventToOption));
        break;
      case 'franchise':
        create$ = this.repo.createFranchise(cleanName).pipe(map(franchiseToOption));
        break;
      case 'label':
      case 'publisher':
        create$ = of({
          id: `${entityType}:${cleanName}`,
          display: cleanName,
          raw: cleanName,
        });
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

    return this.search(entityType, uuid).pipe(
      map((options) => {
        const target = uuid.toLowerCase();
        const match = options.find(
          (o) => (o.id && o.id.toLowerCase() === target) || o.display.toLowerCase() === target,
        );
        if (match) {
          this.cacheOption(entityType, match);
          return match;
        }
        return null;
      }),
      catchError(() => of(null)),
    );
  }
}
