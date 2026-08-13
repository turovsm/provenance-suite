import { Component, SecurityContext, computed, inject, input } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';

marked.setOptions({
  breaks: true,
  gfm: true,
});

@Component({
  selector: 'app-markdown-renderer',
  standalone: true,
  styleUrls: ['./markdown-renderer.component.css'],
  template: `<div class="markdown-rendered-content" [innerHTML]="parsedHtml()"></div>`,
})
export class MarkdownRendererComponent {
  readonly content = input<string | null | undefined>('');
  private readonly sanitizer = inject(DomSanitizer);

  protected readonly parsedHtml = computed<SafeHtml>(() => {
    const raw = this.content();
    if (!raw || !raw.trim()) {
      return '';
    }

    try {
      const rawHtml = marked.parse(raw) as string;

      const sanitized = this.sanitizer.sanitize(SecurityContext.HTML, rawHtml) || '';
      return this.sanitizer.bypassSecurityTrustHtml(sanitized);
    } catch {
      const safeRaw = this.sanitizer.sanitize(SecurityContext.HTML, raw) || '';
      return this.sanitizer.bypassSecurityTrustHtml(safeRaw);
    }
  });
}
