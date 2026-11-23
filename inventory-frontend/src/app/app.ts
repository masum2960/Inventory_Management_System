import { Auth } from './services/auth';
import { Component } from '@angular/core';
import { Dashboard } from './dashboard/dashboard';
import { Products } from './products/products';
import { Login } from './login/login';
import { Categories } from './categories/categories';
import { Suppliers } from './suppliers/suppliers';
import { Users } from './users/users';
import { Register } from './register/register';

@Component({
  selector: 'app-root',
  imports: [Dashboard, Products, Login, Categories, Suppliers, Users, Register],
  templateUrl: './app.html',
  styleUrl: './app.css'
})

export class App {
  currentPage = 'login';

  constructor(public auth: Auth) {}

  
showPage(page: string) {
  if (!this.auth.isLoggedIn() &&
      page !== 'login' &&
      page !== 'register') {
    this.currentPage = 'login';
    return;
  }

  this.currentPage = page;
}


  logout() {
    this.auth.logout();
    this.currentPage = 'login';
}


}
