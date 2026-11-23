
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { forkJoin } from 'rxjs';
import { Auth } from '../services/auth';

@Component({
  selector: 'app-dashboard',
  imports: [],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class Dashboard implements OnInit {

  totalProducts = 0;
  totalCategories = 0;
  totalSuppliers = 0;
  lowStockCount = 0;

  loading = true;
  errorMessage = '';

  constructor(
    private http: HttpClient,
    private auth: Auth,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.loadDashboard();
  }

  loadDashboard() {
    if (!this.auth.isLoggedIn()) {
      this.errorMessage = 'Please log in first.';
      this.loading = false;
      return;
    }

    this.loading = true;
    this.errorMessage = '';

    const headers = this.auth.getAuthHeaders();

    forkJoin({
      categories: this.http.get<any[]>(
        '/api/v1.0/categories', { headers }
      ),
      suppliers: this.http.get<any[]>(
        '/api/v1.0/suppliers', { headers }
      ),
      lowStock: this.http.get<any>(
        '/api/v1.0/products/low-stock', { headers }
      )
    }).subscribe({
      next: (data) => {
        this.totalCategories = data.categories.length;
        this.totalSuppliers = data.suppliers.length;
        this.lowStockCount = data.lowStock.count;

        this.loadProductCount(1, 0);
      },
      error: (error) => {
        console.error(error);
        this.errorMessage = 'Unable to load dashboard data.';
        this.loading = false;
        this.cdr.markForCheck();
      }
    });
  }

  loadProductCount(page: number, count: number) {
    this.http.get<any>(
      '/api/v1.0/products',
      {
        params: { pn: page.toString(), ps: '100' },
        headers: this.auth.getAuthHeaders()
      }
    ).subscribe({
      next: (data) => {
        const products = Array.isArray(data)
          ? data
          : data.products ?? [];

        const total = count + products.length;

        if (products.length === 100) {
          this.loadProductCount(page + 1, total);
        } else {
          this.totalProducts = total;
          this.loading = false;
          this.cdr.markForCheck();
        }
      },
      error: (error) => {
        console.error(error);
        this.errorMessage = 'Unable to load product count.';
        this.loading = false;
        this.cdr.markForCheck();
      }
    });
  }
}
