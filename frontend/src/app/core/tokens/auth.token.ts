import { InjectionToken } from '@angular/core';
import { Observable } from 'rxjs';
import { TokenResponse, UserProfile } from '../../domain/models/auth.model';

export interface AuthRepositoryPort {
  authenticate(email: string, password: string): Observable<TokenResponse>;
  register(email: string, password: string): Observable<UserProfile>;
  fetchIdentityProfile(): Observable<UserProfile>;
}

export const AUTH_REPOSITORY_PORT = new InjectionToken<AuthRepositoryPort>(
  'Core Identity Authentication Infrastructure Port Boundary',
);
