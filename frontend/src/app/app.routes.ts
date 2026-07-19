import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { LoginPageComponent } from './features/auth/components/login-page/login-page.component';
import { DashboardShellComponent } from './features/dashboard/components/dashboard-shell/dashboard-shell.component';

export const routes: Routes = [
  { path: 'login', component: LoginPageComponent },
  {
    path: '',
    component: DashboardShellComponent,
    canActivate: [authGuard],
    children: [],
  },
  { path: '**', redirectTo: 'login' },
];
