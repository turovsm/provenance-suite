import { InjectionToken } from '@angular/core';
import { Observable } from 'rxjs';
import { TokenResponse, UserProfile } from '../../domain/models/auth.model';

export interface AuthRepositoryPort {
  authenticate(email: string, password: string): Observable<TokenResponse>;
  refresh(refreshToken: string): Observable<TokenResponse>;
  register(username: string, email: string, password: string): Observable<UserProfile>;
  logout(refreshToken: string): Observable<void>;
  fetchIdentityProfile(): Observable<UserProfile>;
}

export const AUTH_REPOSITORY_PORT = new InjectionToken<AuthRepositoryPort>(
  'Core Identity Authentication Infrastructure Port Boundary',
);
