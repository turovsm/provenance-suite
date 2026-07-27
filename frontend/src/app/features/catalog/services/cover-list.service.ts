import { Injectable, signal } from '@angular/core';
import { Subject } from 'rxjs';
import { AlbumDetailResponse } from '../../../domain/models/music.model';
import { DraftCoverItem, LocalCoverItem } from '../models/album-form.model';

function randomId(): string {
  return Math.random().toString(36).substring(2, 9);
}

@Injectable()
export class CoverListService {
  private readonly coversSignal = signal<LocalCoverItem[]>([]);
  readonly covers = this.coversSignal.asReadonly();

  readonly changed = new Subject<void>();

  addFiles(files: FileList | File[], coverType: string): void {
    Array.from(files).forEach((file) => this.readAndAppend(file, coverType));
  }

  private readAndAppend(file: File, coverType: string): void {
    if (!file.type.startsWith('image/')) return;
    const previewUrl = URL.createObjectURL(file);

    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const base64 = result.includes(',') ? result.split(',')[1] : result;
      this.coversSignal.update((list) => [
        ...list,
        {
          id: randomId(),
          base64,
          mimeType: file.type || 'image/jpeg',
          fileName: file.name,
          fileSize: file.size,
          coverType,
          previewUrl,
        },
      ]);
      this.changed.next();
    };
    reader.readAsDataURL(file);
  }

  hydrateFromAlbum(covers: AlbumDetailResponse['covers']): void {
    this.revokeAll();
    const items = (covers ?? []).map((c) => {
      const item: LocalCoverItem = {
        id: c.id,
        base64: '',
        mimeType: 'image/jpeg',
        fileName: c.storage_path.split('/').pop() || 'cover.jpg',
        fileSize: 0,
        coverType: c.cover_type || 'Front',
        previewUrl: c.url,
      };

      if (c.url) {
        fetch(c.url)
          .then((res) => res.blob())
          .then((blob) => {
            item.fileSize = blob.size;
            item.mimeType = blob.type || 'image/jpeg';
            const reader = new FileReader();
            reader.onload = () => {
              const resStr = reader.result as string;
              item.base64 = resStr.includes(',') ? resStr.split(',')[1] : resStr;
            };
            reader.readAsDataURL(blob);
          })
          .catch(() => undefined);
      }
      return item;
    });
    this.coversSignal.set(items);
  }

  restoreFromDraft(items: DraftCoverItem[] | undefined): void {
    if (!Array.isArray(items)) return;
    this.coversSignal.set(
      items.map((c) => ({
        id: c.id || randomId(),
        base64: c.base64,
        mimeType: c.mimeType || 'image/jpeg',
        fileName: c.fileName || 'scan.jpg',
        fileSize: c.fileSize || 0,
        coverType: c.coverType || 'Front',
        previewUrl: `data:${c.mimeType || 'image/jpeg'};base64,${c.base64}`,
      })),
    );
  }

  updateType(coverId: string, newType: string): void {
    this.coversSignal.update((list) =>
      list.map((c) => (c.id === coverId ? { ...c, coverType: newType } : c)),
    );
    this.changed.next();
  }

  remove(coverId: string): void {
    const target = this.coversSignal().find((c) => c.id === coverId);
    if (target?.previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(target.previewUrl);
    }
    this.coversSignal.update((list) => list.filter((c) => c.id !== coverId));
    this.changed.next();
  }

  reset(): void {
    this.revokeAll();
    this.coversSignal.set([]);
    this.changed.next();
  }

  revokeAll(): void {
    this.coversSignal().forEach((c) => {
      if (c.previewUrl.startsWith('blob:')) URL.revokeObjectURL(c.previewUrl);
    });
  }

  snapshotForDraft(): DraftCoverItem[] {
    return this.coversSignal().map((c) => ({
      id: c.id,
      base64: c.base64,
      mimeType: c.mimeType,
      fileName: c.fileName,
      fileSize: c.fileSize,
      coverType: c.coverType,
    }));
  }
}
