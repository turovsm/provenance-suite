import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CardActionsComponent } from './card-actions.component';

describe('CardActionsComponent', () => {
  let fixture: ComponentFixture<CardActionsComponent>;
  let component: CardActionsComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CardActionsComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(CardActionsComponent);
    component = fixture.componentInstance;
  });

  it('renders nothing when isSuperuser is false', () => {
    fixture.componentRef.setInput('isSuperuser', false);
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.card-admin-actions')).toBeNull();
  });

  it('renders edit and delete buttons when isSuperuser is true', () => {
    fixture.componentRef.setInput('isSuperuser', true);
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.card-edit-btn')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('.card-delete-btn')).not.toBeNull();
  });

  it('emits edit output and stops event propagation when edit button is clicked', () => {
    const editSpy = vi.fn();
    component.edit.subscribe(editSpy);

    fixture.componentRef.setInput('isSuperuser', true);
    fixture.detectChanges();

    const editBtn = fixture.nativeElement.querySelector('.card-edit-btn') as HTMLButtonElement;
    const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
    const stopSpy = vi.spyOn(clickEvent, 'stopPropagation');
    const preventSpy = vi.spyOn(clickEvent, 'preventDefault');

    editBtn.dispatchEvent(clickEvent);

    expect(stopSpy).toHaveBeenCalled();
    expect(preventSpy).toHaveBeenCalled();
    expect(editSpy).toHaveBeenCalledTimes(1);
  });

  it('emits delete output and stops event propagation when delete button is clicked', () => {
    const deleteSpy = vi.fn();
    component.delete.subscribe(deleteSpy);

    fixture.componentRef.setInput('isSuperuser', true);
    fixture.detectChanges();

    const deleteBtn = fixture.nativeElement.querySelector('.card-delete-btn') as HTMLButtonElement;
    const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
    const stopSpy = vi.spyOn(clickEvent, 'stopPropagation');
    const preventSpy = vi.spyOn(clickEvent, 'preventDefault');

    deleteBtn.dispatchEvent(clickEvent);

    expect(stopSpy).toHaveBeenCalled();
    expect(preventSpy).toHaveBeenCalled();
    expect(deleteSpy).toHaveBeenCalledTimes(1);
  });

  it('shows spinning sync loader and disables buttons when isLoadingEdit is true', () => {
    fixture.componentRef.setInput('isSuperuser', true);
    fixture.componentRef.setInput('isLoadingEdit', true);
    fixture.detectChanges();

    const editBtn = fixture.nativeElement.querySelector('.card-edit-btn') as HTMLButtonElement;
    const deleteBtn = fixture.nativeElement.querySelector('.card-delete-btn') as HTMLButtonElement;

    expect(editBtn.disabled).toBe(true);
    expect(deleteBtn.disabled).toBe(true);
    expect(fixture.nativeElement.querySelector('.spinning')).not.toBeNull();
  });
});
