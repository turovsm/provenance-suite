import { HttpErrorResponse, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { ReplaySubject, catchError, switchMap, take, throwError } from 'rxjs';
import { AUTH_REPOSITORY_PORT } from '../tokens/auth.token';

let refreshInProgress: ReplaySubject<string> | null = null;

function withBearer<T>(req: HttpRequest<T>, token: string): HttpRequest<T> {
  return req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
}

function clearSessionStorage(): void {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const authRepo = inject(AUTH_REPOSITORY_PORT);
  const accessToken = localStorage.getItem('access_token');

  const authReq = accessToken ? withBearer(req, accessToken) : req;

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      const isAuthUrl = req.url.includes('/auth/login') || req.url.includes('/auth/refresh');

      if (error.status !== 401 || isAuthUrl) {
        return throwError(() => error);
      }

      if (refreshInProgress) {
        return refreshInProgress.pipe(
          take(1),
          switchMap((newToken) => next(withBearer(req, newToken))),
        );
      }

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        clearSessionStorage();
        void router.navigate(['/login']);
        return throwError(() => error);
      }

      refreshInProgress = new ReplaySubject<string>(1);
      const pending = refreshInProgress;

      return authRepo.refresh(refreshToken).pipe(
        switchMap((tokens) => {
          localStorage.setItem('access_token', tokens.access_token);
          localStorage.setItem('refresh_token', tokens.refresh_token);

          pending.next(tokens.access_token);
          pending.complete();
          refreshInProgress = null;

          return next(withBearer(req, tokens.access_token));
        }),
        catchError((refreshErr) => {
          pending.error(refreshErr);
          refreshInProgress = null;

          clearSessionStorage();
          void router.navigate(['/login']);
          return throwError(() => refreshErr);
        }),
      );
    }),
  );
};
