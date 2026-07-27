import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthStateEngine } from '../../state/auth.state';

@Component({
  selector: 'app-register-page',
  standalone: true,
  imports: [FormsModule, RouterLink],
  styleUrls: ['./register-page.component.css'],
  templateUrl: './register-page.component.html',
})
export class RegisterPageComponent {
  protected readonly state = inject(AuthStateEngine);

  protected username = '';
  protected email = '';
  protected password = '';
  protected confirmPassword = '';
  protected localValidationError: string | null = null;

  protected handleRegisterSubmit(): void {
    this.localValidationError = null;

    if (!this.username.trim()) {
      this.localValidationError = 'Username is required.';
      return;
    }

    if (!this.email || !this.password) return;

    if (this.password.length < 12) {
      this.localValidationError = 'Password must be at least 12 characters long.';
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.localValidationError = 'Passwords do not match.';
      return;
    }

    this.state.executeRegistrationSequence(this.username, this.email, this.password);
  }
}
