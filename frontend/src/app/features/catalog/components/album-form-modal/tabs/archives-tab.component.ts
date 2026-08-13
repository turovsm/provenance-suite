import { Component, Input, inject } from '@angular/core';
import { FormArray, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { resolveDomainName } from '../../../../../shared/utils/domain-resolver';
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

  protected handleMirrorUrlChange(archiveIndex: number, linkIndex: number, event?: Event): void {
    const linkGroup = this.getArchiveLinks(archiveIndex).at(linkIndex) as FormGroup;
    const urlControl = linkGroup.get('download_url');
    const providerControl = linkGroup.get('provider_name');

    if (!providerControl || !urlControl) return;

    let url = urlControl.value || '';

    if (event) {
      if (event.type === 'paste') {
        const clipboardEvent = event as ClipboardEvent;
        const pastedText = clipboardEvent.clipboardData?.getData('text');
        if (pastedText) {
          url = pastedText;
        }
      } else if (event.target) {
        url = (event.target as HTMLInputElement).value || url;
      }
    }

    const resolved = resolveDomainName(url, 'cloud');
    if (!resolved) return;

    const currentProvider = providerControl.value?.trim() || '';

    if (!currentProvider || currentProvider !== resolved) {
      providerControl.setValue(resolved);
      providerControl.markAsDirty();
    }
  }

  protected handleExternalUrlChange(linkIndex: number, event?: Event): void {
    const linkGroup = this.externalLinks.at(linkIndex) as FormGroup;
    const urlControl = linkGroup.get('url');
    const siteControl = linkGroup.get('site_name');

    if (!siteControl || !urlControl) return;

    let url = urlControl.value || '';

    if (event) {
      if (event.type === 'paste') {
        const clipboardEvent = event as ClipboardEvent;
        const pastedText = clipboardEvent.clipboardData?.getData('text');
        if (pastedText) {
          url = pastedText;
        }
      } else if (event.target) {
        url = (event.target as HTMLInputElement).value || url;
      }
    }

    const resolved = resolveDomainName(url, 'index');
    if (!resolved) return;

    const currentSite = siteControl.value?.trim() || '';

    if (!currentSite || currentSite !== resolved) {
      siteControl.setValue(resolved);
      siteControl.markAsDirty();
    }
  }
}
