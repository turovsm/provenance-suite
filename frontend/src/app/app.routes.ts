import { Routes } from '@angular/router';
import { LoginPageComponent } from './features/auth/components/login-page/login-page.component';

export const routes: Routes = [
  { path: 'login', component: LoginPageComponent },
  { path: '', redirectTo: 'login', pathMatch: 'full' },
];
