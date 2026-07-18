import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { TokenResponse, UserProfile } from '../../domain/models/auth.model';
import { AuthRepositoryPort } from '../tokens/auth.token';

@Injectable({
  providedIn: 'root',
})
export class HttpAuthAdapter implements AuthRepositoryPort {
  private readonly http = inject(HttpClient);
  private readonly endpoint = 'http://localhost:8000/api/v1';

  authenticate(email: string, password: string): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.endpoint}/auth/login`, { email, password });
  }

  fetchIdentityProfile(): Observable<UserProfile> {
    return this.http.get<UserProfile>(`${this.endpoint}/users/me`);
  }
}
