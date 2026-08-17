import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AUTH_REPOSITORY_PORT, AuthRepositoryPort } from '../../../core/tokens/auth.token';
import { UserProfile } from '../../../domain/models/auth.model';
import { AuthStateEngine } from './auth.state';

describe('AuthStateEngine', () => {
  let state: AuthStateEngine;
  let authRepoSpy: Record<keyof AuthRepositoryPort, ReturnType<typeof vi.fn>>;
  let routerSpy: { url: string; navigate: ReturnType<typeof vi.fn> };

  const mockProfile: UserProfile = {
    id: 'u1',
    username: 'archivist',
    email: 'archivist@vault.io',
    is_active: true,
    is_superuser: false,
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
  };

  beforeEach(() => {
    authRepoSpy = {
      authenticate: vi.fn(),
      refresh: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      fetchIdentityProfile: vi.fn(),
    };
    routerSpy = {
      url: '/login',
      navigate: vi.fn().mockResolvedValue(true),
    };

    TestBed.configureTestingModule({
      providers: [
        AuthStateEngine,
        { provide: AUTH_REPOSITORY_PORT, useValue: authRepoSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });

    state = TestBed.inject(AuthStateEngine);
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('executes login sequence, stores tokens, synchronizes profile, and redirects to home', () => {
    authRepoSpy.authenticate.mockReturnValue(
      of({
        access_token: 'acc-123',
        refresh_token: 'ref-123',
        token_type: 'bearer',
        expires_in: 900,
      }),
    );
    authRepoSpy.fetchIdentityProfile.mockReturnValue(of(mockProfile));

    state.executeLoginSequence('archivist@vault.io', 'password123');

    expect(localStorage.getItem('access_token')).toBe('acc-123');
    expect(localStorage.getItem('refresh_token')).toBe('ref-123');
    expect(state.identity()).toEqual(mockProfile);
    expect(state.isAuthenticated()).toBe(true);
    expect(state.isProcessing()).toBe(false);
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/']);
  });

  it('captures authentication errors and resets processing state on login failure', () => {
    authRepoSpy.authenticate.mockReturnValue(
      throwError(() => ({ error: { error: { message: 'Invalid credentials.' } } })),
    );

    state.executeLoginSequence('wrong@vault.io', 'badpass');

    expect(state.authenticationError()).toBe('Invalid credentials.');
    expect(state.isProcessing()).toBe(false);
    expect(state.isAuthenticated()).toBe(false);
  });

  it('executes registration sequence and chains into login', () => {
    authRepoSpy.register.mockReturnValue(of(mockProfile));
    authRepoSpy.authenticate.mockReturnValue(
      of({
        access_token: 'acc-123',
        refresh_token: 'ref-123',
        token_type: 'bearer',
        expires_in: 900,
      }),
    );
    authRepoSpy.fetchIdentityProfile.mockReturnValue(of(mockProfile));

    state.executeRegistrationSequence('archivist', 'archivist@vault.io', 'strongpassword12');

    expect(authRepoSpy.register).toHaveBeenCalledWith(
      'archivist',
      'archivist@vault.io',
      'strongpassword12',
    );
    expect(authRepoSpy.authenticate).toHaveBeenCalledWith('archivist@vault.io', 'strongpassword12');
  });

  it('clears active session, wipes tokens, and navigates to login', () => {
    localStorage.setItem('access_token', 'token');
    localStorage.setItem('refresh_token', 'refresh');
    authRepoSpy.logout.mockReturnValue(of(undefined));

    state.clearActiveSession();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(state.identity()).toBeNull();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
  });
});
