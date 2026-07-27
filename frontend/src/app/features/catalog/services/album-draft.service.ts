import { Injectable } from '@angular/core';
import { ALBUM_DRAFT_STORAGE_KEY } from '../constants/album-form-options';
import { AlbumFormDraft } from '../models/album-form.model';

@Injectable({ providedIn: 'root' })
export class AlbumDraftService {
  persist(draft: AlbumFormDraft): void {
    try {
      localStorage.setItem(ALBUM_DRAFT_STORAGE_KEY, JSON.stringify(draft));
    } catch {
      // Quota exceeded / storage unavailable
    }
  }

  restore(): AlbumFormDraft | null {
    try {
      const raw = localStorage.getItem(ALBUM_DRAFT_STORAGE_KEY);
      if (!raw) return null;
      const draft = JSON.parse(raw);
      if (!draft || typeof draft !== 'object' || !draft.formValue) return null;
      return draft as AlbumFormDraft;
    } catch {
      return null;
    }
  }

  clear(): void {
    localStorage.removeItem(ALBUM_DRAFT_STORAGE_KEY);
  }
}
