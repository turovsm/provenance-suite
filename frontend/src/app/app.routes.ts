import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/components/login-page/login-page.component').then(
        (m) => m.LoginPageComponent,
      ),
  },
  {
    path: 'register',
    loadComponent: () =>
      import('./features/auth/components/register-page/register-page.component').then(
        (m) => m.RegisterPageComponent,
      ),
  },
  {
    path: '',
    loadComponent: () =>
      import('./features/dashboard/components/dashboard-shell/dashboard-shell.component').then(
        (m) => m.DashboardShellComponent,
      ),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./features/catalog/components/album-grid/album-grid.component').then(
            (m) => m.AlbumGridComponent,
          ),
      },
      {
        path: 'events',
        loadComponent: () =>
          import('./features/events/components/event-list/event-list.component').then(
            (m) => m.EventListComponent,
          ),
      },
      {
        path: 'entities',
        loadComponent: () =>
          import('./features/entities/components/entity-directory/entity-directory.component').then(
            (m) => m.EntityDirectoryComponent,
          ),
      },
      {
        path: 'entities/:type/:id',
        loadComponent: () =>
          import('./features/entities/components/entity-detail/entity-detail.component').then(
            (m) => m.EntityDetailComponent,
          ),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
