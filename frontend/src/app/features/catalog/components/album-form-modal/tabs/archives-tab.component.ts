import { Component, Input, inject } from '@angular/core';
import { FormArray, ReactiveFormsModule } from '@angular/forms';
import { AlbumFormBuilderService } from '../../../services/album-form-builder.service';

@Component({
  selector: 'app-archives-tab',
  standalone: true,
  imports: [ReactiveFormsModule],
  styleUrls: ['../album-form-modal.component.css'],
  templateUrl: './archives-tab.component.html',
})
export class ArchivesTabComponent {
  @Input({ required: true }) archives!: FormArray;
  @Input({ required: true }) externalLinks!: FormArray;

  private readonly builder = inject(AlbumFormBuilderService);

  getArchiveLinks(archiveIndex: number): FormArray {
    return this.archives.at(archiveIndex).get('links') as FormArray;
  }

  protected addArchive(): void {
    this.archives.push(this.builder.createArchiveGroup());
  }

  protected removeArchive(index: number): void {
    this.archives.removeAt(index);
  }

  protected addArchiveLink(archiveIndex: number): void {
    this.getArchiveLinks(archiveIndex).push(this.builder.createArchiveLinkGroup());
  }

  protected removeArchiveLink(archiveIndex: number, linkIndex: number): void {
    this.getArchiveLinks(archiveIndex).removeAt(linkIndex);
  }

  protected addExternalLink(): void {
    this.externalLinks.push(this.builder.createExternalLinkGroup());
  }

  protected removeExternalLink(index: number): void {
    this.externalLinks.removeAt(index);
  }
}
