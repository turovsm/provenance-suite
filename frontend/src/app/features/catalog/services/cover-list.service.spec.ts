import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';
import { CoverListService } from './cover-list.service';

describe('CoverListService', () => {
  let service: CoverListService;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [CoverListService] });
    service = TestBed.inject(CoverListService);
  });

  it('adds image files and generates local preview items', () => {
    const mockFile1 = new File(['dummy content 1'], 'front.jpg', { type: 'image/jpeg' });
    const mockFile2 = new File(['dummy content 2'], 'back.jpg', { type: 'image/jpeg' });

    service.addFiles([mockFile1, mockFile2], 'Front');

    expect(service.covers().length).toBe(2);
    expect(service.covers()[0].fileName).toBe('back.jpg'); // Naturally sorted
    expect(service.covers()[1].fileName).toBe('front.jpg');
  });

  it('updates cover type for specific item', () => {
    const mockFile = new File(['data'], 'scan.png', { type: 'image/png' });
    service.addFiles([mockFile], 'Front');

    const id = service.covers()[0].id;
    service.updateType(id, 'Booklet');

    expect(service.covers()[0].coverType).toBe('Booklet');
  });

  it('removes cover by ID and revokes preview URLs', () => {
    const mockFile = new File(['data'], 'scan.jpg', { type: 'image/jpeg' });
    service.addFiles([mockFile], 'Front');
    const id = service.covers()[0].id;

    service.remove(id);

    expect(service.covers().length).toBe(0);
  });
});
