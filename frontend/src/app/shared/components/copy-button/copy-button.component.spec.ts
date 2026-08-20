import { ComponentFixture, TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CopyButtonComponent } from './copy-button.component';

describe('CopyButtonComponent', () => {
  let fixture: ComponentFixture<CopyButtonComponent>;

  beforeEach(async () => {
    vi.useFakeTimers();

    await TestBed.configureTestingModule({
      imports: [CopyButtonComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(CopyButtonComponent);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders default button and title', () => {
    fixture.detectChanges();
    const btn = fixture.nativeElement.querySelector('.copy-btn') as HTMLButtonElement;
    expect(btn).not.toBeNull();
    expect(btn.title).toBe('Copy to clipboard');
    expect(fixture.nativeElement.querySelector('.copied-tooltip')).toBeNull();
  });

  it('writes text to clipboard on click and displays tooltip feedback', async () => {
    const writeTextSpy = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText: writeTextSpy },
    });

    fixture.componentRef.setInput('text', 'secret-passphrase');
    fixture.componentRef.setInput('title', 'Copy Password');
    fixture.detectChanges();

    const btn = fixture.nativeElement.querySelector('.copy-btn') as HTMLButtonElement;
    btn.click();
    await Promise.resolve();
    fixture.detectChanges();

    expect(writeTextSpy).toHaveBeenCalledWith('secret-passphrase');
    expect(fixture.nativeElement.querySelector('.copied-tooltip')?.textContent).toContain('Copied');

    vi.advanceTimersByTime(2000);
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.copied-tooltip')).toBeNull();
  });

  it('does nothing when text input is empty or null', async () => {
    const writeTextSpy = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText: writeTextSpy },
    });

    fixture.componentRef.setInput('text', '');
    fixture.detectChanges();

    const btn = fixture.nativeElement.querySelector('.copy-btn') as HTMLButtonElement;
    btn.click();
    await Promise.resolve();
    fixture.detectChanges();

    expect(writeTextSpy).not.toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('.copied-tooltip')).toBeNull();
  });
});
