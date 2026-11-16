
import { Component, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Auth } from '../services/auth';

@Component({
  selector: 'app-login',
  imports: [FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class Login {

  username = '';
  password = '';
  message = '';
  loading = false;

  constructor(
  private auth: Auth,
  private cdr: ChangeDetectorRef
) {}

  
login() {
  if (this.loading) {
    return;
  }

  this.message = '';
  this.loading = true;

  this.auth.login(this.username, this.password)
    .subscribe({
      next: (response) => {
        console.log('Login response received');

        this.loading = false;
        this.message = 'Login successful!';
        this.password = '';

        this.cdr.markForCheck();
      },
      error: (error) => {
        this.loading = false;
        this.message = 'Login failed. Please check your credentials.';

        console.error('Login error:', error.status);

        this.cdr.markForCheck();
      }
    });
  }
}
