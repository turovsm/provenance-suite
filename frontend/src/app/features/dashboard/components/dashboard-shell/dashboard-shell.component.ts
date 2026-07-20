import { Component, inject, OnInit } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthStateEngine } from '../../../auth/state/auth.state';

@Component({
  selector: 'app-dashboard-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  styleUrls: ['./dashboard-shell.component.css'],
  templateUrl: './dashboard-shell.component.html',
})
export class DashboardShellComponent implements OnInit {
  protected readonly authState = inject(AuthStateEngine);

  protected readonly archiveCategories = [
    { label: 'All Albums', query: 'all', isAll: true, icon: 'apps' },
    { label: 'Rock', query: 'Rock', isAll: false, icon: 'graphic_eq' },
    { label: 'Pop', query: 'Pop', isAll: false, icon: 'music_note' },
    { label: 'J-Pop', query: 'JPop', isAll: false, icon: 'headphones' },
    { label: 'Electronic', query: 'Electronic', isAll: false, icon: 'equalizer' },
    { label: 'Classical', query: 'Classical', isAll: false, icon: 'piano' },
    { label: 'Game OST', query: 'GameOST', isAll: false, icon: 'sports_esports' },
    { label: 'Anime', query: 'Anime', isAll: false, icon: 'tv' },
    { label: 'Soundtrack', query: 'Soundtrack', isAll: false, icon: 'movie' },
    { label: 'Doujin', query: 'Doujin', isAll: false, icon: 'groups' },
    { label: 'Vocaloid', query: 'Vocaloid', isAll: false, icon: 'mic' },
    { label: 'Visual Novels', query: 'VNs', isAll: false, icon: 'menu_book' },
  ];

  ngOnInit(): void {
    if (!this.authState.isAuthenticated()) {
      this.authState.synchronizeProfileState();
    }
  }

  protected executeSignOut(): void {
    this.authState.clearActiveSession();
  }
}
