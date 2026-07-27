import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree } from '@angular/router';
import { vi } from 'vitest';
import { authGuard } from './auth.guard';

describe('authGuard', () => {
  let routerSpy: { createUrlTree: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    routerSpy = { createUrlTree: vi.fn().mockReturnValue({} as UrlTree) };

    TestBed.configureTestingModule({
      providers: [{ provide: Router, useValue: routerSpy }],
    });

    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('allows navigation when access_token exists in storage', () => {
    localStorage.setItem('access_token', 'valid-jwt-token');
    const dummyRoute = {} as ActivatedRouteSnapshot;
    const dummyState = {} as RouterStateSnapshot;
    const result = TestBed.runInInjectionContext(() => authGuard(dummyRoute, dummyState));
    expect(result).toBe(true);
  });

  it('redirects to /login when access_token is missing', () => {
    const dummyRoute = {} as ActivatedRouteSnapshot;
    const dummyState = {} as RouterStateSnapshot;
    TestBed.runInInjectionContext(() => authGuard(dummyRoute, dummyState));
    expect(routerSpy.createUrlTree).toHaveBeenCalledWith(['/login']);
  });
});
