import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { describe, expect, it, afterEach, beforeEach } from 'vitest';
import { HttpAuthAdapter } from './http-auth.adapter';

describe('HttpAuthAdapter', () => {
  let adapter: HttpAuthAdapter;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), HttpAuthAdapter],
    });

    adapter = TestBed.inject(HttpAuthAdapter);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('submits login credentials via HTTP POST', () => {
    adapter.authenticate('collector@vault.io', 'securepassword').subscribe((res) => {
      expect(res.access_token).toBe('mock-access-token');
      expect(res.refresh_token).toBe('mock-refresh-token');
    });

    const req = httpMock.expectOne((r) => r.url.endsWith('/auth/login'));
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ email: 'collector@vault.io', password: 'securepassword' });
    req.flush({
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
      expires_in: 900,
    });
  });

  it('rotates refresh token via HTTP POST', () => {
    adapter.refresh('old-refresh-token').subscribe((res) => {
      expect(res.access_token).toBe('new-access-token');
    });

    const req = httpMock.expectOne((r) => r.url.endsWith('/auth/refresh'));
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ refresh_token: 'old-refresh-token' });
    req.flush({
      access_token: 'new-access-token',
      refresh_token: 'new-refresh-token',
      token_type: 'bearer',
      expires_in: 900,
    });
  });

  it('registers user profile via HTTP POST', () => {
    adapter.register('archivist', 'archivist@vault.io', 'strongpassword').subscribe((user) => {
      expect(user.username).toBe('archivist');
      expect(user.role).toBe('user');
    });

    const req = httpMock.expectOne((r) => r.url.endsWith('/users'));
    expect(req.request.method).toBe('POST');
    req.flush({
      id: 'u1',
      username: 'archivist',
      email: 'archivist@vault.io',
      role: 'user',
      is_active: true,
      created_at: '',
      updated_at: '',
    });
  });

  it('fetches current identity profile via HTTP GET', () => {
    adapter.fetchIdentityProfile().subscribe((user) => {
      expect(user.id).toBe('current-user-uuid');
      expect(user.role).toBe('admin');
    });

    const req = httpMock.expectOne((r) => r.url.endsWith('/users/me'));
    expect(req.request.method).toBe('GET');
    req.flush({
      id: 'current-user-uuid',
      username: 'admin',
      email: 'admin@vault.io',
      role: 'admin',
      is_active: true,
      created_at: '',
      updated_at: '',
    });
  });

  it('terminates active session via HTTP POST logout', () => {
    adapter.logout('valid-refresh-token').subscribe();

    const req = httpMock.expectOne((r) => r.url.endsWith('/auth/logout'));
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ refresh_token: 'valid-refresh-token' });
    req.flush(null);
  });
});
