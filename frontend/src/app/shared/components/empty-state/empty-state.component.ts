import { Component, input } from '@angular/core';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  styleUrls: ['./empty-state.component.css'],
  templateUrl: './empty-state.component.html',
})
export class EmptyStateComponent {
  readonly icon = input<string>('info');
  readonly title = input.required<string>();
  readonly description = input<string | null>(null);
  readonly bordered = input<boolean>(true);
}
