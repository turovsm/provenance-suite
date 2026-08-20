import { Component, HostListener, input, output } from '@angular/core';

@Component({
  selector: 'app-modal-shell',
  standalone: true,
  styleUrls: ['./modal-shell.component.css'],
  templateUrl: './modal-shell.component.html',
})
export class ModalShellComponent {
  readonly title = input.required<string>();
  readonly icon = input<string | null>(null);
  readonly maxWidth = input<string>('620px');
  readonly maxHeight = input<string>('88vh');
  readonly height = input<string>('auto');
  readonly closeOnEscape = input<boolean>(true);
  readonly closeOnBackdrop = input<boolean>(false);

  readonly closed = output<void>();

  @HostListener('window:keydown.escape')
  protected handleEscapeKey(): void {
    if (this.closeOnEscape()) {
      this.close();
    }
  }

  protected handleBackdropClick(event: Event): void {
    if (this.closeOnBackdrop() && event.target === event.currentTarget) {
      this.close();
    }
  }

  protected close(): void {
    this.closed.emit();
  }
}
