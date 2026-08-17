import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, expect, it, vi } from 'vitest';
import { MarkdownRendererComponent } from './markdown-renderer.component';

describe('MarkdownRendererComponent', () => {
  let fixture: ComponentFixture<MarkdownRendererComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarkdownRendererComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(MarkdownRendererComponent);
  });

  it('renders parsed markdown headings, bold text, and lists', () => {
    fixture.componentRef.setInput('content', '# Heading 1\n\n**Bold Text**\n\n- Item 1\n- Item 2');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Heading 1');
    expect(compiled.querySelector('strong')?.textContent).toContain('Bold Text');
    expect(compiled.querySelectorAll('li').length).toBe(2);
  });

  it('sanitizes dangerous script injections while preserving valid markdown', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);

    fixture.componentRef.setInput('content', 'Safe description <script>alert("xss")</script>');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('script')).toBeNull();
    expect(compiled.textContent).toContain('Safe description');

    warnSpy.mockRestore();
  });

  it('renders empty content gracefully without errors', () => {
    fixture.componentRef.setInput('content', '');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.markdown-rendered-content')?.innerHTML).toBe('');
  });
});
