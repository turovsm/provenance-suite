import { ComponentFixture, TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SearchInputComponent } from './search-input.component';

describe('SearchInputComponent', () => {
  let component: SearchInputComponent;
  let fixture: ComponentFixture<SearchInputComponent>;

  beforeEach(async () => {
    vi.useFakeTimers();

    await TestBed.configureTestingModule({
      imports: [SearchInputComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SearchInputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders input with default placeholder', () => {
    const inputEl = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    expect(inputEl.placeholder).toBe('Search...');
  });

  it('emits debounced search query on input', () => {
    const emitSpy = vi.fn();
    component.searchChange.subscribe(emitSpy);

    const inputEl = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    inputEl.value = 'Touhou';
    inputEl.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    expect(emitSpy).not.toHaveBeenCalled();

    vi.advanceTimersByTime(300);

    expect(emitSpy).toHaveBeenCalledWith('Touhou');
  });

  it('clears query and emits empty string immediately when clear button is clicked without double emission', () => {
    const emitSpy = vi.fn();
    component.searchChange.subscribe(emitSpy);

    fixture.componentRef.setInput('value', 'ZUN');
    fixture.detectChanges();

    const clearBtn = fixture.nativeElement.querySelector('.clear-btn') as HTMLButtonElement;
    expect(clearBtn).not.toBeNull();

    clearBtn.click();
    fixture.detectChanges();

    vi.advanceTimersByTime(0);

    expect(emitSpy).toHaveBeenCalledTimes(1);
    expect(emitSpy).toHaveBeenCalledWith('');
    expect(fixture.nativeElement.querySelector('input').value).toBe('');

    vi.advanceTimersByTime(300);
    expect(emitSpy).toHaveBeenCalledTimes(1);
  });
});
