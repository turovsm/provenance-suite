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
    { label: 'Commercial Pop/Rock', query: 'Pop' },
    { label: 'Electronic Streams', query: 'Electronic' },
    { label: 'Soundtrack Archives', query: 'Soundtrack' },
    { label: 'Independent Circles', query: 'Doujin' },
    { label: 'Vocaloid Synthesis', query: 'Vocaloid' },
    { label: 'Visual Novel Media', query: 'VNs' },
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
