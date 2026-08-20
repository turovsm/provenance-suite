import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ModalShellComponent } from './modal-shell.component';

describe('ModalShellComponent', () => {
  let component: ModalShellComponent;
  let fixture: ComponentFixture<ModalShellComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ModalShellComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ModalShellComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('title', 'Test Modal Header');
    fixture.componentRef.setInput('icon', 'edit');
    fixture.detectChanges();
  });

  it('renders title and icon properly in header', () => {
    const titleEl = fixture.nativeElement.querySelector('h2');
    const iconEl = fixture.nativeElement.querySelector('.header-icon');

    expect(titleEl.textContent).toContain('Test Modal Header');
    expect(iconEl.textContent).toContain('edit');
  });

  it('emits closed event when close button is clicked', () => {
    const closeSpy = vi.fn();
    component.closed.subscribe(closeSpy);

    const closeBtn = fixture.nativeElement.querySelector('.close-btn') as HTMLButtonElement;
    closeBtn.click();

    expect(closeSpy).toHaveBeenCalledTimes(1);
  });

  it('emits closed event when Escape key is pressed', () => {
    const closeSpy = vi.fn();
    component.closed.subscribe(closeSpy);

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));

    expect(closeSpy).toHaveBeenCalledTimes(1);
  });

  it('does not emit closed event on Escape when closeOnEscape is false', () => {
    fixture.componentRef.setInput('closeOnEscape', false);
    fixture.detectChanges();

    const closeSpy = vi.fn();
    component.closed.subscribe(closeSpy);

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));

    expect(closeSpy).not.toHaveBeenCalled();
  });

  it('handles backdrop click based on closeOnBackdrop setting', () => {
    const closeSpy = vi.fn();
    component.closed.subscribe(closeSpy);

    const backdropEl = fixture.nativeElement.querySelector('.modal-backdrop') as HTMLElement;
    backdropEl.click();
    expect(closeSpy).not.toHaveBeenCalled();

    fixture.componentRef.setInput('closeOnBackdrop', true);
    fixture.detectChanges();

    backdropEl.click();
    expect(closeSpy).toHaveBeenCalledTimes(1);
  });

  it('prevents default wheel event when scrolling directly on backdrop', () => {
    const backdropEl = fixture.nativeElement.querySelector('.modal-backdrop') as HTMLElement;
    const wheelEvent = new WheelEvent('wheel', { bubbles: true, cancelable: true });
    const preventSpy = vi.spyOn(wheelEvent, 'preventDefault');

    backdropEl.dispatchEvent(wheelEvent);

    expect(preventSpy).toHaveBeenCalled();
  });
});
