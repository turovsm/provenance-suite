import { Component, computed, input } from '@angular/core';

export type AlertType = 'error' | 'warning' | 'info';

@Component({
  selector: 'app-error-banner',
  standalone: true,
  styleUrls: ['./error-banner.component.css'],
  templateUrl: './error-banner.component.html',
})
export class ErrorBannerComponent {
  readonly message = input<string | null | undefined>(null);
  readonly type = input<AlertType>('error');

  protected readonly iconName = computed(() => {
    switch (this.type()) {
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      case 'error':
      default:
        return 'error';
    }
  });
}
