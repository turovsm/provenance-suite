import { Component, OnDestroy, input, signal } from '@angular/core';

@Component({
  selector: 'app-copy-button',
  standalone: true,
  styleUrls: ['./copy-button.component.css'],
  templateUrl: './copy-button.component.html',
})
export class CopyButtonComponent implements OnDestroy {
  readonly text = input<string | null | undefined>(null);
  readonly title = input<string>('Copy to clipboard');
  readonly timeoutMs = input<number>(2000);

  protected readonly isCopied = signal<boolean>(false);
  private timeoutId: ReturnType<typeof setTimeout> | null = null;

  ngOnDestroy(): void {
    this.clearTimer();
  }

  protected copy(event: MouseEvent): void {
    event.stopPropagation();
    event.preventDefault();

    const value = this.text();
    if (!value) return;

    if (navigator?.clipboard?.writeText) {
      navigator.clipboard
        .writeText(value)
        .then(() => this.showCopiedFeedback())
        .catch(() => undefined);
    }
  }

  private showCopiedFeedback(): void {
    this.clearTimer();
    this.isCopied.set(true);

    this.timeoutId = setTimeout(() => {
      this.isCopied.set(false);
      this.timeoutId = null;
    }, this.timeoutMs());
  }

  private clearTimer(): void {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
  }
}
