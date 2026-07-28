import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, of } from 'rxjs';
import { AUTH_REPOSITORY_PORT } from '../../../core/tokens/auth.token';
import { UserProfile } from '../../../domain/models/auth.model';
import { extractErrorMessage } from '../../../shared/utils/error-extractor';

@Injectable({
  providedIn: 'root',
})
export class AuthStateEngine {
  private readonly router = inject(Router);
  private readonly repo = inject(AUTH_REPOSITORY_PORT);

  private readonly currentProfileSignal = signal<UserProfile | null>(null);
  private readonly activeErrorSignal = signal<string | null>(null);
  private readonly processingSignal = signal<boolean>(false);

  readonly identity = computed(() => this.currentProfileSignal());
  readonly authenticationError = computed(() => this.activeErrorSignal());
  readonly isProcessing = computed(() => this.processingSignal());
  readonly isAuthenticated = computed(() => this.currentProfileSignal() !== null);

  executeLoginSequence(email: string, password: string): void {
    this.processingSignal.set(true);
    this.activeErrorSignal.set(null);

    this.repo
      .authenticate(email, password)
      .pipe(
        catchError((err) => {
          const message = extractErrorMessage(err, 'Identity validation connection failed.');
          this.activeErrorSignal.set(message);
          this.processingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((response) => {
        if (!response) return;

        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);
        this.synchronizeProfileState();
      });
  }

  executeRegistrationSequence(username: string, email: string, password: string): void {
    this.processingSignal.set(true);
    this.activeErrorSignal.set(null);

    this.repo
      .register(username, email, password)
      .pipe(
        catchError((err) => {
          const message = extractErrorMessage(err, 'Account registration sequence failed.');
          this.activeErrorSignal.set(message);
          this.processingSignal.set(false);
          return of(null);
        }),
      )
      .subscribe((profile) => {
        if (!profile) return;
        this.executeLoginSequence(email, password);
      });
  }

  synchronizeProfileState(): void {
    this.repo
      .fetchIdentityProfile()
      .pipe(
        catchError(() => {
          this.clearActiveSession();
          return of(null);
        }),
      )
      .subscribe((profile) => {
        if (!profile) return;
        this.currentProfileSignal.set(profile);
        this.processingSignal.set(false);
        void this.router.navigate(['/']);
      });
  }

  clearActiveSession(): void {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      this.repo
        .logout(refreshToken)
        .pipe(catchError(() => of(null)))
        .subscribe();
    }

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.currentProfileSignal.set(null);
    this.processingSignal.set(false);
    void this.router.navigate(['/login']);
  }
}
