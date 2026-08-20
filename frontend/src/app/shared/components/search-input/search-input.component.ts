import {
  Component,
  DestroyRef,
  OnInit,
  effect,
  inject,
  input,
  output,
  signal,
  untracked,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

@Component({
  selector: 'app-search-input',
  standalone: true,
  styleUrls: ['./search-input.component.css'],
  templateUrl: './search-input.component.html',
})
export class SearchInputComponent implements OnInit {
  readonly placeholder = input<string>('Search...');
  readonly value = input<string>('');
  readonly debounceMs = input<number>(300);

  readonly searchChange = output<string>();

  private readonly destroyRef = inject(DestroyRef);
  private readonly searchSubject$ = new Subject<string>();

  protected readonly query = signal<string>('');

  constructor() {
    effect(() => {
      const externalVal = this.value();
      untracked(() => {
        this.query.set(externalVal);
      });
    });
  }

  ngOnInit(): void {
    this.searchSubject$
      .pipe(
        debounceTime(this.debounceMs()),
        distinctUntilChanged(),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((term) => {
        this.searchChange.emit(term);
      });
  }

  protected onInput(event: Event): void {
    const val = (event.target as HTMLInputElement).value;
    this.query.set(val);
    this.searchSubject$.next(val);
  }

  protected clear(): void {
    this.query.set('');
    this.searchSubject$.next('');
    this.searchChange.emit('');
  }
}
