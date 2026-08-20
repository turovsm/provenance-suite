import { ComponentFixture, TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';
import { ErrorBannerComponent } from './error-banner.component';

describe('ErrorBannerComponent', () => {
  let fixture: ComponentFixture<ErrorBannerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ErrorBannerComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ErrorBannerComponent);
  });

  it('renders nothing when message is null or empty', () => {
    fixture.componentRef.setInput('message', null);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.error-banner')).toBeNull();

    fixture.componentRef.setInput('message', '');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.error-banner')).toBeNull();
  });

  it('renders error message and icon by default', () => {
    fixture.componentRef.setInput('message', 'Database connection offline.');
    fixture.detectChanges();

    const banner = fixture.nativeElement.querySelector('.error-banner');
    expect(banner).not.toBeNull();
    expect(banner.classList.contains('type-error')).toBe(true);
    expect(banner.textContent).toContain('Database connection offline.');
    expect(fixture.nativeElement.querySelector('.icon-alert')?.textContent).toContain('error');
  });

  it('renders warning and info types correctly', () => {
    fixture.componentRef.setInput('message', 'Warning alert');
    fixture.componentRef.setInput('type', 'warning');
    fixture.detectChanges();

    let banner = fixture.nativeElement.querySelector('.error-banner');
    expect(banner.classList.contains('type-warning')).toBe(true);
    expect(fixture.nativeElement.querySelector('.icon-alert')?.textContent).toContain('warning');

    fixture.componentRef.setInput('message', 'Info note');
    fixture.componentRef.setInput('type', 'info');
    fixture.detectChanges();

    banner = fixture.nativeElement.querySelector('.error-banner');
    expect(banner.classList.contains('type-info')).toBe(true);
    expect(fixture.nativeElement.querySelector('.icon-alert')?.textContent).toContain('info');
  });
});
