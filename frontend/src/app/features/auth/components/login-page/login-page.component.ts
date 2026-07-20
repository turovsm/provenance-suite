import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthStateEngine } from '../../state/auth.state';
import { LoginFormComponent } from '../login-form/login-form.component';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [LoginFormComponent, RouterLink],
  styleUrls: ['./login-page.component.css'],
  templateUrl: './login-page.component.html',
})
export class LoginPageComponent {
  protected readonly state = inject(AuthStateEngine);

  protected executeAuthenticationRequest(credentials: { email: string; password: string }): void {
    this.state.executeLoginSequence(credentials.email, credentials.password);
  }
}
