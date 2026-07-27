import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { TokenResponse, UserProfile } from '../../domain/models/auth.model';
import { AuthRepositoryPort } from '../tokens/auth.token';

@Injectable({
  providedIn: 'root',
})
export class HttpAuthAdapter implements AuthRepositoryPort {
  private readonly http = inject(HttpClient);
  private readonly endpoint = environment.apiBaseUrl;

  authenticate(email: string, password: string): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.endpoint}/auth/login`, { email, password });
  }

  refresh(refreshToken: string): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.endpoint}/auth/refresh`, {
      refresh_token: refreshToken,
    });
  }

  register(username: string, email: string, password: string): Observable<UserProfile> {
    return this.http.post<UserProfile>(`${this.endpoint}/users`, { username, email, password });
  }

  logout(refreshToken: string): Observable<void> {
    return this.http.post<void>(`${this.endpoint}/auth/logout`, {
      refresh_token: refreshToken,
    });
  }

  fetchIdentityProfile(): Observable<UserProfile> {
    return this.http.get<UserProfile>(`${this.endpoint}/users/me`);
  }
}
