import { ComponentFixture, TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { AlbumCardComponent } from './album-card.component';

describe('AlbumCardComponent', () => {
  let component: AlbumCardComponent;
  let fixture: ComponentFixture<AlbumCardComponent>;

  const mockAlbum = {
    id: 'a1',
    title_original: 'Scarlet Devil OST',
    aliases: ['Embodiment of Scarlet Devil'],
    release_year: 2002,
    release_month: 8,
    release_day: 11,
    label: null,
    publisher: null,
    original_folder_name: 'TH06_OST',
    album_artist: { id: 'art1', name_original: 'ZUN', name_translated: null },
    total_discs: 1,
    covers: [
      {
        id: 'c1',
        storage_path: 'covers/a1/c1.jpg',
        thumbhash: null,
        url: 'http://cdn/covers/a1/c1.jpg',
        cover_type: 'Front',
        created_at: null,
      },
    ],
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AlbumCardComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(AlbumCardComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('album', mockAlbum);
    fixture.detectChanges();
  });

  it('renders title, artist name, and formatted release date', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.title-primary')?.textContent).toContain('Scarlet Devil OST');
    expect(compiled.querySelector('.artists-line')?.textContent).toContain('ZUN');
    expect(compiled.querySelector('.release-date')?.textContent).toContain('2002.08.11');
  });

  it('emits cardClicked when clicked', () => {
    const emitSpy = vi.spyOn(component.cardClicked, 'emit');
    const cardEl = fixture.nativeElement.querySelector('.glass-album-card');
    cardEl.click();

    expect(emitSpy).toHaveBeenCalledWith('a1');
  });

  it('shows admin actions only when isSuperuser signal is true', () => {
    expect(fixture.nativeElement.querySelector('.card-admin-actions')).toBeNull();

    fixture.componentRef.setInput('isSuperuser', true);
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.card-admin-actions')).not.toBeNull();
  });
});
