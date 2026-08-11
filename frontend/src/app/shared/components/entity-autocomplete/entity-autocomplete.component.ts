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

  @Output() optionSelected = new EventEmitter<AutocompleteOption>();

  private readonly entitySearch = inject(EntitySearchService);
  private readonly elementRef = inject(ElementRef);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly inputQuery = signal<string>('');
  protected readonly options = signal<AutocompleteOption[]>([]);
  protected readonly isOpen = signal<boolean>(false);
  private selectedOptionId: string | null = null;

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
    this.selectedOptionId = null;
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
      if (match.id) {
        this.selectedOptionId = match.id;
        this.onChange(match.id);
      }
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
    this.selectedOptionId = option.id ?? null;
    this.isOpen.set(false);
    if (option.id) {
      this.entitySearch.cacheOption(this.entityType, option);
    }
    const val = option.id || option.display;
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
          this.selectOption(created);
        } else {
          this.onChange(name);
          this.onTouched();
          this.isOpen.set(false);
        }
      },
      error: () => {
        this.onChange(name);
        this.onTouched();
        this.isOpen.set(false);
      },
    });
  }

  writeValue(value: unknown): void {
    if (typeof value === 'string') {
      if (UUID_PATTERN.test(value)) {
        this.selectedOptionId = value;
        this.resolveUuidDisplayName(value);
      } else {
        this.selectedOptionId = null;
        this.inputQuery.set(value);
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
      if (obj.id) this.selectedOptionId = obj.id;
      const displayStr = obj.display || obj.name_original || obj.short_name || '';
      this.inputQuery.set(displayStr);
      if (obj.id && displayStr) {
        this.entitySearch.cacheOption(this.entityType, {
          id: obj.id,
          display: displayStr,
          raw: obj as unknown as AutocompleteEntity,
        });
      }
      return;
    }

    this.selectedOptionId = null;
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
