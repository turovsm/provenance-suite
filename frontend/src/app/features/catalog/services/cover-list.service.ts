import { Injectable, signal } from '@angular/core';
import { Subject } from 'rxjs';
import { AlbumDetailResponse } from '../../../domain/models/music.model';
import { LocalCoverItem } from '../models/album-form.model';

function randomId(): string {
  return Math.random().toString(36).substring(2, 9);
}

@Injectable()
export class CoverListService {
  private readonly coversSignal = signal<LocalCoverItem[]>([]);
  readonly covers = this.coversSignal.asReadonly();

  readonly changed = new Subject<void>();

  addFiles(files: FileList | File[], coverType: string): void {
    const newItems: LocalCoverItem[] = [];

    Array.from(files).forEach((file) => {
      if (!file.type.startsWith('image/')) return;

      newItems.push({
        id: randomId(),
        file,
        base64: '',
        mimeType: file.type || 'image/jpeg',
        fileName: file.name,
        fileSize: file.size,
        coverType,
        previewUrl: URL.createObjectURL(file),
      });
    });

    if (newItems.length > 0) {
      this.coversSignal.update((list) => [...list, ...newItems]);
      this.changed.next();
    }
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
}
