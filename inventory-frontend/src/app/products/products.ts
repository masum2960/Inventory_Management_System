import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Auth } from '../services/auth';
import { FormsModule } from '@angular/forms';
@Component({
  selector: 'app-products',
  imports: [FormsModule],
  templateUrl: './products.html',
  styleUrl: './products.css'
})
export class Products implements OnInit {

  products: any[] = [];
  errorMessage = '';
  searchTerm = '';
  filteredProducts: any[] = [];
  constructor(private http: HttpClient, 
    private auth: Auth,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.http.get<any>('/api/v1.0/products', {
      headers: this.auth.getAuthHeaders()
    }).subscribe({
      next: (data) => {
        this.products = Array.isArray(data)
          ? data
          : data.products ?? [];
        this.filteredProducts = this.products;
        console.log('Products loaded:', this.products);
        console.log('First product:', this.products[0]);
        console.log('Category details:', this.products[0]?.category);
        console.log('Stock details:', this.products[0]?.stock);

        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error('Error loading products:', error);
        this.errorMessage = 'Unable to load products from the API.';

        this.cdr.markForCheck();
      }
    });
  }

  searchProducts(): void {
    const term = this.searchTerm.toLowerCase().trim();

    this.filteredProducts = this.products.filter(product =>
      product.name.toLowerCase().includes(term)
    );
  }

  showAddForm = false;



newProduct = {
  product_id: '',
  sku: '',
  name: '',
  category: '',
  supplier: '',
  price: 0,
  quantity: 0,
  min_level: 0
};

saveMessage = '';
saving = false;



toggleAddForm() {
  this.showAddForm = !this.showAddForm;
}
}
