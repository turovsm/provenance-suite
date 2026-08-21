import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AUTH_REPOSITORY_PORT } from '../tokens/auth.token';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let authRepoSpy: { refresh: ReturnType<typeof vi.fn> };
  let routerSpy: { navigate: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    authRepoSpy = { refresh: vi.fn() };
    routerSpy = { navigate: vi.fn() };

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: AUTH_REPOSITORY_PORT, useValue: authRepoSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });

    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
    localStorage.clear();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('attaches Bearer token header when access_token is present in storage', () => {
    localStorage.setItem('access_token', 'my-access-token');

    http.get('/api/v1/albums').subscribe();

    const req = httpMock.expectOne('/api/v1/albums');
    expect(req.request.headers.get('Authorization')).toBe('Bearer my-access-token');
    req.flush({});
  });

  it('triggers token refresh and retries failed request on 401 response', () => {
    localStorage.setItem('access_token', 'expired-access-token');
    localStorage.setItem('refresh_token', 'valid-refresh-token');

    authRepoSpy.refresh.mockReturnValue(
      of({
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer',
        expires_in: 900,
      }),
    );

    http.get('/api/v1/albums').subscribe();

    const firstReq = httpMock.expectOne('/api/v1/albums');
    firstReq.flush({ message: 'Expired' }, { status: 401, statusText: 'Unauthorized' });

    expect(authRepoSpy.refresh).toHaveBeenCalledWith('valid-refresh-token');
    expect(localStorage.getItem('access_token')).toBe('new-access-token');

    const retriedReq = httpMock.expectOne('/api/v1/albums');
    expect(retriedReq.request.headers.get('Authorization')).toBe('Bearer new-access-token');
    retriedReq.flush({ items: [] });
  });

  it('redirects to / and clears storage when refresh token is missing or fails', () => {
    localStorage.setItem('access_token', 'expired-access-token');
    authRepoSpy.refresh.mockReturnValue(throwError(() => new Error('Revoked')));

    http.get('/api/v1/albums').subscribe({
      error: (err) => expect(err).toBeTruthy(),
    });

    const req = httpMock.expectOne('/api/v1/albums');
    req.flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(routerSpy.navigate).toHaveBeenCalledWith(['/']);
    expect(localStorage.getItem('access_token')).toBeNull();
  });
});
