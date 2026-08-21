import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';
import { EntityAvatarComponent } from './entity-avatar.component';

describe('EntityAvatarComponent', () => {
  let fixture: ComponentFixture<EntityAvatarComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EntityAvatarComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(EntityAvatarComponent);
  });

  it('renders mapped fallback icon when no image URL is provided', () => {
    fixture.componentRef.setInput('entityType', 'artist');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.fallback-icon')?.textContent).toContain('person');

    fixture.componentRef.setInput('entityType', 'franchise');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.fallback-icon')?.textContent).toContain(
      'sports_esports',
    );

    fixture.componentRef.setInput('entityType', 'label');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.fallback-icon')?.textContent).toContain('album');

    fixture.componentRef.setInput('entityType', 'publisher');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.fallback-icon')?.textContent).toContain('domain');
  });

  it('applies artist circular masking for artist entity type and rectangular for others', () => {
    fixture.componentRef.setInput('entityType', 'artist');
    fixture.detectChanges();

    const frame = fixture.nativeElement.querySelector('.avatar-frame') as HTMLElement;
    expect(frame.classList.contains('artist-avatar')).toBe(true);
    expect(frame.classList.contains('logo-avatar')).toBe(false);

    fixture.componentRef.setInput('entityType', 'label');
    fixture.detectChanges();

    expect(frame.classList.contains('artist-avatar')).toBe(false);
    expect(frame.classList.contains('logo-avatar')).toBe(true);
  });

  it('renders image element when imageUrl is present and falls back on error event', () => {
    fixture.componentRef.setInput('imageUrl', 'https://example.com/avatar.jpg');
    fixture.componentRef.setInput('name', '上海アリス幻樂団');
    fixture.detectChanges();

    let imgEl = fixture.nativeElement.querySelector('img') as HTMLImageElement;
    expect(imgEl).not.toBeNull();
    expect(imgEl.src).toContain('https://example.com/avatar.jpg');
    expect(imgEl.alt).toBe('上海アリス幻樂団');

    imgEl.dispatchEvent(new Event('error'));
    fixture.detectChanges();

    imgEl = fixture.nativeElement.querySelector('img');
    expect(imgEl).toBeNull();
    expect(fixture.nativeElement.querySelector('.fallback-icon')).not.toBeNull();
  });

  it('applies correct size classes and dimensions based on input', () => {
    fixture.componentRef.setInput('size', 'lg');
    fixture.componentRef.setInput('imageUrl', 'https://example.com/avatar.jpg');
    fixture.detectChanges();

    const frame = fixture.nativeElement.querySelector('.avatar-frame') as HTMLElement;
    expect(frame.classList.contains('size-lg')).toBe(true);

    const imgEl = fixture.nativeElement.querySelector('img') as HTMLImageElement;
    expect(imgEl.getAttribute('width')).toBe('140');
    expect(imgEl.getAttribute('height')).toBe('140');
  });
});
