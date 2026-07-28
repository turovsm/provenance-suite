import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { AUTH_REPOSITORY_PORT } from './core/tokens/auth.token';
import { ALBUM_REPOSITORY_PORT } from './core/tokens/album.token';
import { HttpAuthAdapter } from './core/adapters/http-auth.adapter';
import { HttpAlbumAdapter } from './core/adapters/http-album.adapter';
import { authInterceptor } from './core/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    { provide: AUTH_REPOSITORY_PORT, useClass: HttpAuthAdapter },
    { provide: ALBUM_REPOSITORY_PORT, useClass: HttpAlbumAdapter },
  ],
};
