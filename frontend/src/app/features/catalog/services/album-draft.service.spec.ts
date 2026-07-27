import { TestBed } from '@angular/core/testing';
import { AlbumDraftService } from './album-draft.service';
import { ALBUM_DRAFT_STORAGE_KEY } from '../constants/album-form-options';
import { AlbumFormDraft } from '../models/album-form.model';

describe('AlbumDraftService', () => {
  let service: AlbumDraftService;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [AlbumDraftService] });
    service = TestBed.inject(AlbumDraftService);
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('persists and restores form draft payload from localStorage', () => {
    const mockDraft: AlbumFormDraft = {
      formValue: { title_original: 'Drafted Album' },
      coversList: [],
    };

    service.persist(mockDraft);
    const restored = service.restore();

    expect(restored).not.toBeNull();
    expect(restored?.formValue.title_original).toBe('Drafted Album');
  });

  it('clears persisted draft on command', () => {
    localStorage.setItem(ALBUM_DRAFT_STORAGE_KEY, JSON.stringify({ formValue: {} }));
    service.clear();
    expect(service.restore()).toBeNull();
  });
});
