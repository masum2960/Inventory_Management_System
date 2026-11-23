import { FormsModule } from '@angular/forms';
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Auth } from '../services/auth';

@Component({
  selector: 'app-users',
  imports: [FormsModule],
  templateUrl: './users.html',
  styleUrl: './users.css'
})
export class Users implements OnInit {

  users: any[] = [];
  filteredUsers: any[] = [];
  searchTerm = '';
  errorMessage = '';

  pageNumber = 1;
  pageSize = 10;


editingUserId = '';
savingEdit = false;
deletingId = '';
userMessage = '';

editUser = {
  name: '',
  email: ''
};


  constructor(
    private http: HttpClient,
    private auth: Auth,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.loadUsers();
  }

  loadUsers() {
    this.http.get<any[]>('/api/v1.0/users', {
      headers: this.auth.getAuthHeaders()
    }).subscribe({
      next: (data) => {
        this.users = data;
        this.errorMessage = '';
        this.searchUsers();
        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error(error);
        this.errorMessage = error.status === 403
          ? 'Admin access is required.'
          : 'Unable to load users.';
        this.cdr.markForCheck();
      }
    });
  }

  searchUsers() {
    const term = this.searchTerm.toLowerCase().trim();

    this.filteredUsers = this.users.filter(user =>
      (user.name || '').toLowerCase().includes(term) ||
      (user.user_id || '').toLowerCase().includes(term) ||
      (user.email || '').toLowerCase().includes(term)
    );

    this.pageNumber = 1;
  }

  get pagedUsers() {
    const start = (this.pageNumber - 1) * this.pageSize;
    return this.filteredUsers.slice(start, start + this.pageSize);
  }

  nextPage() {
    if (this.pageNumber * this.pageSize < this.filteredUsers.length) {
      this.pageNumber++;
    }
  }

  previousPage() {
    if (this.pageNumber > 1) {
      this.pageNumber--;
    }
  }


startEdit(user: any) {
  this.editingUserId = user.user_id;
  this.userMessage = '';

  this.editUser = {
    name: user.name || '',
    email: user.email || ''
  };
}

saveEdit() {
  if (!this.editUser.name.trim() ||
      !this.editUser.email.trim()) {
    this.userMessage = 'Name and Email are required.';
    return;
  }

  this.savingEdit = true;
  this.userMessage = '';

  const data = {
    name: this.editUser.name.trim(),
    email: this.editUser.email.trim()
  };

  this.http.put<any>(
    '/api/v1.0/users/' +
      encodeURIComponent(this.editingUserId),
    data,
    { headers: this.auth.getAuthHeaders() }
  ).subscribe({
    next: () => {
      this.savingEdit = false;
      this.editingUserId = '';
      this.userMessage = 'User updated successfully!';
      this.loadUsers();
      this.cdr.markForCheck();
    },
    error: (error) => {
      this.savingEdit = false;
      this.userMessage =
        error.error?.error || 'Unable to update user.';
      this.cdr.markForCheck();
    }
  });
}

deleteUser(user: any) {
  if (!confirm('Delete user ' + user.user_id + '?')) {
    return;
  }

  this.deletingId = user.user_id;
  this.userMessage = '';

  this.http.delete<any>(
    '/api/v1.0/users/' +
      encodeURIComponent(user.user_id),
    { headers: this.auth.getAuthHeaders() }
  ).subscribe({
    next: () => {
      this.deletingId = '';
      this.userMessage = 'User deleted successfully!';
      this.loadUsers();
      this.cdr.markForCheck();
    },
    error: (error) => {
      this.deletingId = '';
      this.userMessage =
        error.error?.error || 'Unable to delete user.';
      this.cdr.markForCheck();
    }
  });
}

}
