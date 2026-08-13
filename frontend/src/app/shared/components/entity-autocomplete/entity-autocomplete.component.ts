import {
  Component,
  DestroyRef,
  ElementRef,
  EventEmitter,
  HostBinding,
  HostListener,
  Input,
  OnInit,
  Output,
  forwardRef,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import {
  AutocompleteEntity,
  AutocompleteOption,
  EntityType,
} from '../../models/autocomplete.model';
import { EntitySearchService } from '../../services/entity-search.service';

export type { AutocompleteOption, EntityType } from '../../models/autocomplete.model';

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

type OnChangeFn = (value: string | null) => void;
type OnTouchedFn = () => void;

@Component({
  selector: 'app-entity-autocomplete',
  standalone: true,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => EntityAutocompleteComponent),
      multi: true,
    },
  ],
  styleUrls: ['./entity-autocomplete.component.css', '../dropdown-overlay.styles.css'],
  templateUrl: './entity-autocomplete.component.html',
})
export class EntityAutocompleteComponent implements OnInit, ControlValueAccessor {
  @Input() entityType: EntityType = 'artist';
  @Input() placeholder = 'Type to search master entities...';
  @Input() canCreate = true;
  @Input() dense = false;
  @Input() bindValue: 'id' | 'display' = 'id';

  @Output() optionSelected = new EventEmitter<AutocompleteOption>();

  private readonly entitySearch = inject(EntitySearchService);
  private readonly elementRef = inject(ElementRef);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly inputQuery = signal<string>('');
  protected readonly options = signal<AutocompleteOption[]>([]);
  protected readonly isOpen = signal<boolean>(false);

  @HostBinding('class.open-autocomplete') get isAutocompleteOpen() {
    return this.isOpen();
  }

  private readonly searchSubject$ = new Subject<string>();

  private onChange: OnChangeFn = () => undefined;
  private onTouched: OnTouchedFn = () => undefined;

  ngOnInit(): void {
    this.searchSubject$
      .pipe(
        debounceTime(200),
        distinctUntilChanged(),
        switchMap((q) => this.entitySearch.search(this.entityType, q)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((opts) => {
        this.options.set(opts);
        this.checkExactMatchAndEmit(this.inputQuery());
      });
  }

  protected onInput(event: Event): void {
    const val = (event.target as HTMLInputElement).value;
    this.inputQuery.set(val);
    this.isOpen.set(true);
    this.searchSubject$.next(val);
    this.onChange(val);
    this.checkExactMatchAndEmit(val);
  }

  private checkExactMatchAndEmit(query: string): void {
    const trimmed = query.trim().toLowerCase();
    if (!trimmed) return;
    const match = this.options().find((o) => o.display.trim().toLowerCase() === trimmed);
    if (match) {
      const val = this.bindValue === 'display' ? match.display : match.id || match.display;
      this.onChange(val);
      this.optionSelected.emit(match);
    }
  }

  protected openDropdown(): void {
    this.isOpen.set(true);
    this.searchSubject$.next(this.inputQuery());
    setTimeout(() => {
      this.elementRef.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 50);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.isOpen.set(false);
      this.onTouched();
    }
  }

  protected hasExactMatch(): boolean {
    const q = this.inputQuery().trim().toLowerCase();
    return this.options().some((o) => o.display.toLowerCase() === q);
  }

  protected isOptionSelected(option: AutocompleteOption): boolean {
    return this.inputQuery().trim().toLowerCase() === option.display.trim().toLowerCase();
  }

  protected selectOption(option: AutocompleteOption): void {
    this.inputQuery.set(option.display);
    this.isOpen.set(false);

    this.entitySearch.cacheOption(this.entityType, option);

    this.options.update((curr) => {
      const exists = curr.some(
        (o) =>
          (o.id && option.id && o.id === option.id) ||
          o.display.toLowerCase() === option.display.toLowerCase(),
      );
      return exists ? curr : [...curr, option];
    });

    const val = this.bindValue === 'display' ? option.display : option.id || option.display;
    this.onChange(val);
    this.onTouched();
    this.optionSelected.emit(option);
  }

  protected createNewEntity(): void {
    const name = this.inputQuery().trim();
    if (!name) return;

    this.entitySearch.create(this.entityType, name).subscribe({
      next: (created) => {
        if (created) {
          this.entitySearch.cacheOption(this.entityType, created);

          this.options.update((curr) => {
            const exists = curr.some(
              (o) =>
                (o.id && created.id && o.id === created.id) ||
                o.display.toLowerCase() === created.display.toLowerCase(),
            );
            return exists ? curr : [...curr, created];
          });

          this.selectOption(created);
        } else {
          const fallbackVal = name;
          this.onChange(fallbackVal);
          this.onTouched();
          this.isOpen.set(false);
        }
      },
      error: () => {
        const fallbackVal = name;
        this.onChange(fallbackVal);
        this.onTouched();
        this.isOpen.set(false);
      },
    });
  }

  writeValue(value: unknown): void {
    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (!trimmed) {
        this.inputQuery.set('');
        return;
      }

      if (UUID_PATTERN.test(trimmed)) {
        this.resolveUuidDisplayName(trimmed);
      } else {
        this.inputQuery.set(trimmed);
        const opt: AutocompleteOption = {
          id: `${this.entityType}:${trimmed}`,
          display: trimmed,
          raw: trimmed,
        };
        this.entitySearch.cacheOption(this.entityType, opt);
        this.options.update((curr) => {
          const exists = curr.some((o) => o.display.toLowerCase() === trimmed.toLowerCase());
          return exists ? curr : [...curr, opt];
        });
      }
      return;
    }

    if (value && typeof value === 'object') {
      const obj = value as {
        id?: string;
        display?: string;
        name_original?: string;
        short_name?: string;
      };
      const displayStr = obj.display || obj.name_original || obj.short_name || '';
      this.inputQuery.set(displayStr);
      if (displayStr) {
        const opt: AutocompleteOption = {
          id: obj.id || `${this.entityType}:${displayStr}`,
          display: displayStr,
          raw: obj as unknown as AutocompleteEntity,
        };
        this.entitySearch.cacheOption(this.entityType, opt);
        this.options.update((curr) => {
          const exists = curr.some((o) => o.display.toLowerCase() === displayStr.toLowerCase());
          return exists ? curr : [...curr, opt];
        });
      }
      return;
    }

    this.inputQuery.set('');
  }

  private resolveUuidDisplayName(uuid: string): void {
    this.entitySearch.resolveById(this.entityType, uuid).subscribe((found) => {
      if (found) {
        this.inputQuery.set(found.display);
        if (this.entityType === 'artist') {
          this.optionSelected.emit(found);
        }
      } else if (!this.inputQuery()) {
        this.inputQuery.set('');
      }
    });
  }

  registerOnChange(fn: OnChangeFn): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: OnTouchedFn): void {
    this.onTouched = fn;
  }
}
