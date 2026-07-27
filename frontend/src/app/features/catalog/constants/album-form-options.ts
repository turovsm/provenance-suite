import { SelectOption } from '../../../shared/components/custom-select/custom-select.component';

export const ALBUM_DRAFT_STORAGE_KEY = 'provenance_album_ingest_draft_v3';

export const MEDIA_TYPES = ['CD', 'DVD', 'BD', 'Cassette', 'Vinyl', 'Web'];

export const CONTAINER_FORMATS = ['Tracks', 'ISO', 'MDF', 'BIN_CUE', 'CDI', 'IMG', 'VOB'];

export const LOG_TYPE_OPTIONS: SelectOption[] = [
  { label: 'None / Unlogged', value: '' },
  { label: 'EAC', value: 'EAC' },
  { label: 'XLD', value: 'XLD' },
  { label: 'EZCD', value: 'EZCD' },
  { label: 'CUERipper', value: 'CUERipper' },
  { label: 'cyanrip', value: 'cyanrip' },
  { label: 'whipper', value: 'whipper' },
];

export const AUDIO_CODECS = ['FLAC', 'MP3', 'ALAC', 'AAC', 'PCM', 'AC3', 'DTS', 'WMA', 'WavPack'];

export const VIDEO_CODEC_OPTIONS: SelectOption[] = [
  { label: 'No Video', value: '' },
  { label: 'MPEG2', value: 'MPEG2' },
  { label: 'H264', value: 'H264' },
  { label: 'HEVC', value: 'HEVC' },
  { label: 'VC1', value: 'VC1' },
];

export const BITRATE_MODE_OPTIONS: SelectOption[] = [
  { label: 'Bitrate Mode', value: '' },
  { label: 'CBR', value: 'CBR' },
  { label: 'VBR', value: 'VBR' },
  { label: 'ABR', value: 'ABR' },
];

export const COVER_TYPES = ['Front', 'Back', 'Booklet', 'Disc', 'Inlay', 'Matrix', 'Other'];

export const TRACK_ARTIST_ROLES = [
  'Composer',
  'Arranger',
  'Vocalist',
  'Voicebank',
  'Lyricist',
  'Performer',
  'Mixer',
];
