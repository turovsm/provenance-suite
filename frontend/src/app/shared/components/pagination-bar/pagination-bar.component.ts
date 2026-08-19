import { Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CustomSelectComponent, SelectOption } from '../custom-select/custom-select.component';

@Component({
  selector: 'app-pagination-bar',
  standalone: true,
  imports: [FormsModule, CustomSelectComponent],
  styleUrls: ['./pagination-bar.component.css'],
  templateUrl: './pagination-bar.component.html',
})
export class PaginationBarComponent {
  readonly currentPage = input.required<number>();
  readonly totalPages = input.required<number>();
  readonly totalCount = input.required<number>();
  readonly pageSize = input<number>(24);
  readonly pageSizeOptions = input<SelectOption[]>([]);
  readonly itemLabel = input<string>('item');
  readonly itemPluralLabel = input<string | null>(null);

  readonly pageChange = output<number>();
  readonly pageSizeChange = output<number>();

  protected handlePageSizeChange(value: string | null): void {
    if (value) {
      this.pageSizeChange.emit(Number(value));
    }
  }
}
