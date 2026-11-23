import { Component,ChangeDetectorRef,Output,EventEmitter} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-register',
  imports: [FormsModule],
  templateUrl: './register.html',
  styleUrl: './register.css'
})
export class Register {

  user = {
    user_id: '',
    name: '',
    email: '',
    password: ''
  };

  confirmPassword = '';
  saving = false;
  successMessage = '';
  errorMessage = '';
  registered = false;

  @Output() loginClick = new EventEmitter<void>();
  
  openLogin() {
    this.loginClick.emit();
}

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  register() {
    this.errorMessage = '';
    this.successMessage = '';

    if (!this.user.user_id.trim() ||
        !this.user.name.trim() ||
        !this.user.email.trim() ||
        !this.user.password) {
      this.errorMessage = 'Please fill in all fields.';
      return;
    }

    if (this.user.password.length < 8) {
      this.errorMessage = 'Password must be at least 8 characters.';
      return;
    }

    if (this.user.password !== this.confirmPassword) {
      this.errorMessage = 'Passwords do not match.';
      return;
    }

    const data = {
      user_id: this.user.user_id.trim(),
      name: this.user.name.trim(),
      email: this.user.email.trim(),
      password: this.user.password
    };

    this.saving = true;

    this.http.post<any>(
      '/api/v1.0/register',
      data
    ).subscribe({
      next: () => {
        this.successMessage =
          'Registration successful! You can now log in.';
        this.registered = true;
        this.saving = false;
        this.cdr.markForCheck();
      },
      error: (error) => {
        this.errorMessage =
          error.error?.error || 'Registration failed.';
        this.saving = false;
        this.cdr.markForCheck();
      }
    });
  }
}
