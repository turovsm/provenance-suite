import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-card-actions',
  standalone: true,
  styleUrls: ['./card-actions.component.css'],
  templateUrl: './card-actions.component.html',
})
export class CardActionsComponent {
  readonly isSuperuser = input<boolean>(false);
  readonly isLoadingEdit = input<boolean>(false);
  readonly editLabel = input<string>('Edit');
  readonly deleteLabel = input<string>('Delete');

  readonly edit = output<void>();
  readonly delete = output<void>();

  protected handleEdit(event: MouseEvent): void {
    event.stopPropagation();
    event.preventDefault();
    if (this.isLoadingEdit()) return;
    this.edit.emit();
  }

  protected handleDelete(event: MouseEvent): void {
    event.stopPropagation();
    event.preventDefault();
    if (this.isLoadingEdit()) return;
    this.delete.emit();
  }
}
