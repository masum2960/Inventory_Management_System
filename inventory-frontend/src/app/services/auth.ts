
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { tap } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class Auth {

  private authHeader = '';

  constructor(private http: HttpClient) {}

  login(username: string, password: string) {
    const credentials = btoa(username + ':' + password);

    const headers = new HttpHeaders({
      Authorization: 'Basic ' + credentials
    });

    return this.http.post<any>(
      '/api/v1.0/login',
      {},
      { headers }
    ).pipe(
      tap(() => {
        this.authHeader = 'Basic ' + credentials;
      })
    );
  }

  getAuthHeaders() {
    return new HttpHeaders({
      Authorization: this.authHeader
    });
  }

  isLoggedIn() {
    return this.authHeader !== '';
  }

  logout() {
    this.authHeader = '';
  }
}
