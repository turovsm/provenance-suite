import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';
import { EmptyStateComponent } from './empty-state.component';

describe('EmptyStateComponent', () => {
  let fixture: ComponentFixture<EmptyStateComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EmptyStateComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(EmptyStateComponent);
  });

  it('renders title, icon, and description', () => {
    fixture.componentRef.setInput('title', 'No Records Found');
    fixture.componentRef.setInput('icon', 'search_off');
    fixture.componentRef.setInput('description', 'Try adjusting your search criteria.');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h3')?.textContent).toContain('No Records Found');
    expect(compiled.querySelector('.empty-icon')?.textContent).toContain('search_off');
    expect(compiled.querySelector('p')?.textContent).toContain(
      'Try adjusting your search criteria.',
    );
  });

  it('applies bordered class by default and removes when set to false', () => {
    fixture.componentRef.setInput('title', 'Empty');
    fixture.detectChanges();

    const card = fixture.nativeElement.querySelector('.empty-state-card') as HTMLElement;
    expect(card.classList.contains('bordered')).toBe(true);

    fixture.componentRef.setInput('bordered', false);
    fixture.detectChanges();

    expect(card.classList.contains('bordered')).toBe(false);
  });

  it('renders cleanly without description when not provided', () => {
    fixture.componentRef.setInput('title', 'Empty List');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('p')).toBeNull();
  });
});
