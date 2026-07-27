import { MasterArtist, MasterEvent, MasterFranchise } from '../../domain/models/music.model';

export type EntityType = 'artist' | 'event' | 'franchise' | 'label' | 'publisher';

export type AutocompleteEntity = MasterArtist | MasterEvent | MasterFranchise | string;

export interface AutocompleteOption {
  id?: string;
  display: string;
  subValue?: string;
  raw: AutocompleteEntity;
}
