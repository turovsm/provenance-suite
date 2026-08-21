import { UpperCasePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthStateEngine } from '../../../auth/state/auth.state';

@Component({
  selector: 'app-dashboard-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, UpperCasePipe],
  styleUrls: ['./dashboard-shell.component.css'],
  templateUrl: './dashboard-shell.component.html',
})
export class DashboardShellComponent implements OnInit {
  protected readonly authState = inject(AuthStateEngine);

  ngOnInit(): void {
    if (!this.authState.isAuthenticated()) {
      this.authState.synchronizeProfileState();
    }
  }

  protected executeSignOut(): void {
    this.authState.clearActiveSession();
  }
}
