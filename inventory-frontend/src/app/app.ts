import { Component } from '@angular/core';
import { Dashboard } from './dashboard/dashboard';
import { Products } from './products/products';
import { Login } from './login/login';

@Component({
  selector: 'app-root',
  imports: [Dashboard, Products, Login],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  currentPage = 'dashboard';

  showPage(page: string) {
    this.currentPage = page;
  }
}
