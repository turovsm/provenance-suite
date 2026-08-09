import {
  Component,
  ElementRef,
  EventEmitter,
  Output,
  ViewChild,
  forwardRef,
  signal,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'app-aliases-chip-input',
  standalone: true,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => AliasesChipInputComponent),
      multi: true,
    },
  ],
  template: `
    <div
      class="aliases-input-container"
      role="button"
      tabindex="0"
      (click)="focusInput()"
      (keydown.enter)="focusInput()"
    >
      @for (alias of aliases(); track alias; let i = $index) {
        <span class="alias-chip">
          {{ alias }}
          <button
            type="button"
            class="alias-chip-remove"
            (click)="removeAlias(i); $event.stopPropagation()"
            title="Remove alias"
          >
            <span class="material-symbols-outlined alias-chip-remove-icon">close</span>
          </button>
        </span>
      }
      <input
        #inputEl
        type="text"
        class="alias-text-input"
        [placeholder]="placeholder"
        [value]="draft"
        (input)="draft = $any($event.target).value"
        (keydown)="onKeydown($event)"
        (blur)="onTouched()"
      />
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
        width: 100%;
      }
      .aliases-input-container {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.4rem;
        padding: 0.45rem 0.6rem;
        background-color: rgba(255, 255, 255, 0.015);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 4px;
        transition: all 0.2s ease;
        cursor: text;
      }
      .aliases-input-container:focus-within {
        border-color: var(--accent-blue);
        box-shadow: 0 0 0 3px var(--border-focus-glow);
      }
      .alias-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.2rem 0.5rem;
        background-color: rgba(56, 189, 248, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 4px;
        color: var(--accent-blue);
        font-family: var(--font-mono), monospace;
        font-size: 0.72rem;
        font-weight: 500;
      }
      .alias-chip-remove {
        background: none;
        border: none;
        color: var(--accent-blue);
        cursor: pointer;
        padding: 0;
        display: flex;
        align-items: center;
        opacity: 0.7;
        transition: all 0.15s ease;
      }
      .alias-chip-remove:hover {
        opacity: 1;
        color: var(--accent-error);
      }
      .alias-chip-remove-icon {
        font-size: 14px;
      }
      .alias-text-input {
        flex: 1;
        min-width: 120px;
        background: transparent;
        border: none;
        outline: none;
        color: var(--text-primary);
        font-size: 0.8rem;
        padding: 0.25rem 0;
      }
      .alias-text-input::placeholder {
        color: rgba(255, 255, 255, 0.25);
      }
    `,
  ],
})
export class AliasesChipInputComponent implements ControlValueAccessor {
  placeholder = 'Type alias and press Enter...';

  /** Emits the full alias list whenever the user adds or removes a chip. */
  @Output() aliasesChanged = new EventEmitter<string[]>();

  protected aliases = signal<string[]>([]);
  protected draft = '';

  @ViewChild('inputEl') inputEl?: ElementRef<HTMLInputElement>;

  private onChange: (value: string[]) => void = () => undefined;
  protected onTouched: () => void = () => undefined;

  writeValue(value: string[] | null): void {
    this.aliases.set(Array.isArray(value) ? [...value] : []);
  }

  registerOnChange(fn: (value: string[]) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  protected onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      event.preventDefault();
      const value = this.draft.trim();
      if (value) {
        this.addAlias(value);
      }
    } else if (event.key === 'Backspace' && this.draft === '' && this.aliases().length > 0) {
      this.removeAlias(this.aliases().length - 1);
    }
  }

  protected addAlias(value: string): void {
    const cleaned = value.trim();
    this.draft = '';
    if (!cleaned) return;
    const current = this.aliases();
    if (current.some((a) => a.toLowerCase() === cleaned.toLowerCase())) return;
    const next = [...current, cleaned];
    this.aliases.set(next);
    this.onChange(next);
    this.aliasesChanged.emit(next);
  }

  protected removeAlias(index: number): void {
    const next = this.aliases().filter((_, i) => i !== index);
    this.aliases.set(next);
    this.onChange(next);
    this.onTouched();
    this.aliasesChanged.emit(next);
  }

  protected focusInput(): void {
    this.inputEl?.nativeElement.focus();
  }
}
