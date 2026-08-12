import { DatePipe, KeyValuePipe, NgClass } from '@angular/common';
import { Component, HostListener, inject, signal } from '@angular/core';
import {
  AlbumChangeEntry,
  AlbumDetailResponse,
  ArtistDetailResponse,
  TrackDetailResponse,
} from '../../../../domain/models/music.model';

export interface TrackCreditGroup {
  role: string;
  artists: ArtistDetailResponse[];
}

const ROLE_CLASS_MAP: Record<string, string> = {
  composer: 'role-composer',
  arranger: 'role-arranger',
  vocalist: 'role-vocal',
  performer: 'role-vocal',
  voicebank: 'role-voicebank',
  lyricist: 'role-lyricist',
  mixer: 'role-mixer',
};
import { AlbumStateEngine } from '../../state/album.state';

@Component({
  selector: 'app-album-detail-drawer',
  standalone: true,
  imports: [DatePipe, KeyValuePipe, NgClass],
  styleUrls: ['./album-detail-drawer.component.css'],
  templateUrl: './album-detail-drawer.component.html',
})
export class AlbumDetailDrawerComponent {
  protected readonly state = inject(AlbumStateEngine);

  protected readonly activeDiscIndex = signal<number>(0);
  protected readonly activeInspectorTab = signal<
    'cue' | 'log' | 'accuraterip' | 'changelog' | null
  >(null);
  protected readonly copiedField = signal<string | null>(null);

  protected readonly expandedChangelogId = signal<string | null>(null);

  @HostListener('window:keydown.escape')
  protected handleEscapeKey(): void {
    this.close();
  }

  protected toggleChangelog(id: string): void {
    this.expandedChangelogId.set(this.expandedChangelogId() === id ? null : id);
  }

  protected isComplexChange(val: unknown): val is AlbumChangeEntry {
    return !!val && typeof val === 'object' && 'type' in val;
  }

  protected getChangeTypeClass(val: unknown): string {
    return this.isComplexChange(val) ? `type-${val.type}` : '';
  }

  protected toggleInspector(tab: 'cue' | 'log' | 'accuraterip' | 'changelog'): void {
    this.activeInspectorTab.set(this.activeInspectorTab() === tab ? null : tab);
  }

  protected getCoverUrl(album: AlbumDetailResponse): string | null {
    if (!album.covers || album.covers.length === 0) return null;
    const front = album.covers.find((c) => c.cover_type.toLowerCase() === 'front');
    return front ? front.url : album.covers[0].url;
  }

  protected getFormattedReleaseDate(album: AlbumDetailResponse): string | null {
    if (!album.release_year) return null;
    const y = album.release_year.toString();
    const m = album.release_month ? album.release_month.toString().padStart(2, '0') : null;
    const d = album.release_day ? album.release_day.toString().padStart(2, '0') : null;
    if (m && d) return `${y}/${m}/${d}`;
    if (m) return `${y}/${m}`;
    return y;
  }

  protected groupTrackCredits(track: TrackDetailResponse): TrackCreditGroup[] {
    const groups = new Map<string, ArtistDetailResponse[]>();
    for (const artist of track.artists ?? []) {
      const role = artist.role?.trim() || 'Credited';
      const bucket = groups.get(role);
      if (bucket) {
        bucket.push(artist);
      } else {
        groups.set(role, [artist]);
      }
    }
    return Array.from(groups, ([role, artists]) => ({ role, artists }));
  }

  protected roleClass(role: string): string {
    return ROLE_CLASS_MAP[role.trim().toLowerCase()] ?? 'role-generic';
  }

  protected logScoreClass(score: number): string {
    if (score >= 100) return 'score-perfect';
    if (score >= 0) return 'score-partial';
    return 'score-negative';
  }

  protected getTrackSpecs(track: TrackDetailResponse): string {
    const parts: string[] = [];
    if (track.audio_codec) parts.push(track.audio_codec);
    if (track.video_codec) parts.push(`Video: ${track.video_codec}`);
    if (track.bit_depth && track.sample_rate) {
      parts.push(`${track.bit_depth}bit / ${track.sample_rate / 1000}kHz`);
    }
    if (track.bitrate_kbps) {
      const mode = track.bitrate_mode ? ` ${track.bitrate_mode}` : '';
      parts.push(`${track.bitrate_kbps}kbps${mode}`);
    }
    return parts.join(' • ') || 'FLAC';
  }

  protected handleBackdropClick(event: Event): void {
    if (event.target === event.currentTarget) {
      this.close();
    }
  }

  protected close(): void {
    this.state.clearSelectedAlbum();
  }

  protected selectDisc(index: number): void {
    this.activeDiscIndex.set(index);
    this.activeInspectorTab.set(null);
  }

  protected copyToClipboard(text: string, fieldIdentifier: string): void {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      this.copiedField.set(fieldIdentifier);
      setTimeout(() => {
        if (this.copiedField() === fieldIdentifier) {
          this.copiedField.set(null);
        }
      }, 2000);
    });
  }

  protected formatDuration(totalSeconds: number | null): string {
    if (totalSeconds === null || totalSeconds === undefined) return '--:--';
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }

  protected formatBytes(bytes: number | null): string {
    if (bytes === null || bytes === undefined || bytes === 0) return 'Unknown Size';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  }
}
