export type LibraryCategory =
  | 'Rock'
  | 'Pop'
  | 'Electronic'
  | 'Classical'
  | 'Soundtrack'
  | 'GameOST'
  | 'Doujin'
  | 'Vocaloid'
  | 'Anime'
  | 'JPop'
  | 'VNs';

export interface AlbumSummary {
  id: string;
  title_original: string;
  title_translated: string | null;
  release_date: string | null;
  library_category: LibraryCategory;
  original_folder_name: string;
  total_discs: number;
  has_cover: boolean;
}

export interface PaginatedAlbumsResponse {
  items: AlbumSummary[];
  total_count: number;
  limit: number;
  offset: number;
}
