import { Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ErrorBannerComponent } from '../../../../shared/components/error-banner/error-banner.component';

@Component({
  selector: 'app-login-form',
  standalone: true,
  imports: [FormsModule, ErrorBannerComponent],
  styleUrls: ['./login-form.component.css'],
  templateUrl: './login-form.component.html',
})
export class LoginFormComponent {
  readonly isDisabled = input<boolean>(false);
  readonly errorMessage = input<string | null>(null);

  readonly submitted = output<{ email: string; password: string }>();

  protected emailCredentials = '';
  protected passwordCredentials = '';

  protected handleFormSubmit(): void {
    if (!this.emailCredentials || !this.passwordCredentials) return;
    this.submitted.emit({
      email: this.emailCredentials,
      password: this.passwordCredentials,
    });
  }
}
