import {
  Component,
  ElementRef,
  HostBinding,
  HostListener,
  Input,
  computed,
  forwardRef,
  inject,
  signal,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

export interface SelectOption {
  label: string;
  value: string;
}

type OnChangeFn = (value: string | null) => void;
type OnTouchedFn = () => void;

@Component({
  selector: 'app-custom-select',
  standalone: true,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => CustomSelectComponent),
      multi: true,
    },
  ],
  styleUrls: ['./custom-select.component.css', '../dropdown-overlay.styles.css'],
  templateUrl: './custom-select.component.html',
})
export class CustomSelectComponent implements ControlValueAccessor {
  @Input() placeholder = 'Select option...';
  @Input() dense = false;
  @Input() openUp = false;
  @Input() direction: 'down' | 'up' = 'down';

  private readonly normalizedOpts = signal<SelectOption[]>([]);
  @Input({ required: true }) set options(val: (string | SelectOption)[]) {
    if (!val) {
      this.normalizedOpts.set([]);
      return;
    }
    this.normalizedOpts.set(
      val.map((item) => (typeof item === 'string' ? { label: item || 'None', value: item } : item)),
    );
  }

  private readonly elementRef = inject(ElementRef);

  protected readonly selectedValue = signal<string | null>(null);
  protected readonly isOpen = signal<boolean>(false);
  protected readonly isDisabled = signal<boolean>(false);

  @HostBinding('class.open-select') get isSelectOpen() {
    return this.isOpen();
  }

  protected get isOpeningUp(): boolean {
    return this.openUp || this.direction === 'up';
  }

  protected readonly normalizedOptions = computed(() => this.normalizedOpts());

  protected readonly selectedLabel = computed(() => {
    const val = this.selectedValue();
    const found = this.normalizedOpts().find((o) => o.value === val);
    if (found) return found.label;
    return val !== null && val !== undefined ? String(val) : '';
  });

  private onChange: OnChangeFn = () => undefined;
  private onTouched: OnTouchedFn = () => undefined;

  toggleOpen(): void {
    if (this.isDisabled()) return;
    const opening = !this.isOpen();
    this.isOpen.set(opening);
    if (opening) {
      setTimeout(() => {
        this.elementRef.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }, 50);
    }
  }

  selectOption(opt: SelectOption): void {
    if (this.isDisabled()) return;
    this.selectedValue.set(opt.value);
    this.onChange(opt.value);
    this.onTouched();
    this.isOpen.set(false);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.isOpen.set(false);
    }
  }

  writeValue(value: string | null): void {
    this.selectedValue.set(value);
  }

  registerOnChange(fn: OnChangeFn): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: OnTouchedFn): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.isDisabled.set(isDisabled);
    if (isDisabled) {
      this.isOpen.set(false);
    }
  }
}
