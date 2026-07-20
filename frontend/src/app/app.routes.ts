import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { LoginPageComponent } from './features/auth/components/login-page/login-page.component';
import { RegisterPageComponent } from './features/auth/components/register-page/register-page.component';
import { DashboardShellComponent } from './features/dashboard/components/dashboard-shell/dashboard-shell.component';
import { AlbumGridComponent } from './features/catalog/components/album-grid/album-grid.component';

export const routes: Routes = [
  { path: 'login', component: LoginPageComponent },
  { path: 'register', component: RegisterPageComponent },
  {
    path: '',
    component: DashboardShellComponent,
    canActivate: [authGuard],
    children: [
      { path: '', component: AlbumGridComponent },
      { path: 'collections/:category', component: AlbumGridComponent },
    ],
  },
  { path: '**', redirectTo: 'login' },
];
