import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  const tokenExists = !!localStorage.getItem('access_token');

  if (!tokenExists) {
    router.navigate(['/login']);
    return false;
  }

  return true;
};
