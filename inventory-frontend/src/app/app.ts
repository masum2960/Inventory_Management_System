
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
  imports: [
    Dashboard,
    Products,
    Login,
    Categories,
    Suppliers,
    Users,
    Register
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  currentPage = 'login';

  selectedStockProductId: string | null = null;

  constructor(public auth: Auth) {}

  showPage(page: string) {
    if (!this.auth.isLoggedIn() &&
        page !== 'login' &&
        page !== 'register') {
      this.currentPage = 'login';
      return;
    }

    this.selectedStockProductId = null;
    this.currentPage = page;
  }

  openLowStockProduct(productId: string) {
    if (!this.auth.isLoggedIn()) {
      this.currentPage = 'login';
      return;
    }

    this.selectedStockProductId = productId;
    this.currentPage = 'products';
  }

  logout() {
    this.auth.logout();
    this.selectedStockProductId = null;
    this.currentPage = 'login';
  }
}
