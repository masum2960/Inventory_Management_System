
import { Component, OnInit, ChangeDetectorRef, Input } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { Auth } from '../services/auth';

@Component({
  selector: 'app-products',
  imports: [FormsModule],
  templateUrl: './products.html',
  styleUrl: './products.css'
})
export class Products implements OnInit {

  @Input() stockProductId: string | null = null;

  products: any[] = [];
  filteredProducts: any[] = [];

  errorMessage = '';
  searchTerm = '';

  showAddForm = false;
  saving = false;
  saveMessage = '';

  // Add Product
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

  // Edit and Delete Product
  editingProductId = '';
  editMessage = '';
  savingEdit = false;
  deletingId = '';

  editProduct = {
    sku: '',
    name: '',
    category: '',
    supplier: '',
    price: 0
  };

  pageNumber = 1;
  pageSize = 10;
  hasNextPage = false;
  isSearching = false;

  // Stock Update
  selectedStockProduct: any = null;
  stockSaving = false;
  stockMessage = '';

  stockChange = {
    type: 'received',
    quantity: 1,
    warehouse: '',
    reason: ''
  };

  // Stock History
  selectedHistoryProduct = '';
  stockMovements: any[] = [];
  historyMessage = '';

  constructor(
    private http: HttpClient,
    public auth: Auth,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    if (this.stockProductId) {
      this.loadSelectedProduct(this.stockProductId);
    } else {
      this.loadProducts(1);
    }
  }

  // Open product selected from Dashboard
  loadSelectedProduct(productId: string) {
    if (!this.auth.isLoggedIn()) {
      this.errorMessage = 'Please log in to view products.';
      return;
    }

    this.isSearching = true;
    this.errorMessage = '';

    this.http.get<any>(
      '/api/v1.0/products/' + encodeURIComponent(productId),
      { headers: this.auth.getAuthHeaders() }
    ).subscribe({
      next: (product) => {
        this.searchTerm = product.name ?? '';
        this.filteredProducts = [product];

        this.openStockForm(product);

        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error(error);

        this.errorMessage = error.status === 404
          ? 'Product not found.'
          : 'Unable to open the selected product.';

        this.cdr.markForCheck();
      }
    });
  }

  // Load Products
  loadProducts(page: number) {
    if (!this.auth.isLoggedIn()) {
      this.errorMessage = 'Please log in to view products.';
      return;
    }

    this.errorMessage = '';

    this.http.get<any>(
      `/api/v1.0/products?pn=${page}&ps=${this.pageSize}`,
      { headers: this.auth.getAuthHeaders() }
    ).subscribe({
      next: (data) => {
        this.products = Array.isArray(data)
          ? data
          : data.products ?? [];

        this.pageNumber = page;
        this.hasNextPage = this.products.length === this.pageSize;

        this.searchProducts();
        this.cdr.markForCheck();
      },
      error: (error) => {
        this.errorMessage = 'Unable to load products.';
        console.error(error);
        this.cdr.markForCheck();
      }
    });
  }

  nextPage() {
    this.loadProducts(this.pageNumber + 1);
  }

  previousPage() {
    if (this.pageNumber > 1) {
      this.loadProducts(this.pageNumber - 1);
    }
  }

  // Search loaded products
  searchProducts() {
    const term = this.searchTerm.toLowerCase().trim();

    this.filteredProducts = this.products.filter(product =>
      product.name.toLowerCase().includes(term)
    );
  }

  // Add Product Form
  toggleAddForm() {
    this.showAddForm = !this.showAddForm;
    this.saveMessage = '';
  }

  // Save Product
  saveProduct() {
    this.saveMessage = '';

    if (!this.auth.isLoggedIn()) {
      this.saveMessage = 'Please log in first.';
      return;
    }

    if (
      !this.newProduct.product_id.trim() ||
      !this.newProduct.sku.trim() ||
      !this.newProduct.name.trim() ||
      !this.newProduct.category.trim() ||
      !this.newProduct.supplier.trim()
    ) {
      this.saveMessage = 'Please fill in all fields.';
      return;
    }

    const price = Number(this.newProduct.price);
    const quantity = Number(this.newProduct.quantity);
    const minLevel = Number(this.newProduct.min_level);

    if (
      !Number.isFinite(price) || price < 0 ||
      !Number.isInteger(quantity) || quantity < 0 ||
      !Number.isInteger(minLevel) || minLevel < 0
    ) {
      this.saveMessage = 'Please enter valid price and stock values.';
      return;
    }

    const productData = {
      product_id: this.newProduct.product_id.trim(),
      sku: this.newProduct.sku.trim(),
      name: this.newProduct.name.trim(),
      category: {
        name: this.newProduct.category.trim()
      },
      supplier: {
        name: this.newProduct.supplier.trim()
      },
      price: price,
      stock: {
        quantity: quantity,
        min_level: minLevel,
        locations: [
          {
            warehouse: 'WH-MAIN',
            quantity: quantity
          }
        ]
      }
    };

    this.saving = true;

    this.http.post<any>(
      '/api/v1.0/products',
      productData,
      { headers: this.auth.getAuthHeaders() }
    ).subscribe({
      next: (product) => {
        this.saving = false;
        this.saveMessage = 'Product added successfully!';

        this.products.push(product);
        this.searchProducts();

        this.newProduct = {
          product_id: '',
          sku: '',
          name: '',
          category: '',
          supplier: '',
          price: 0,
          quantity: 0,
          min_level: 0
        };

        this.cdr.markForCheck();
      },
      error: (error) => {
        this.saving = false;

        this.saveMessage =
          error.error?.error || 'Unable to save product.';

        console.error('Save Product error:', error.status);
        this.cdr.markForCheck();
      }
    });
  }

  // Edit Product
  startEdit(product: any) {
    this.showAddForm = false;
    this.editMessage = '';
    this.editingProductId = product.product_id;

    this.editProduct = {
      sku: product.sku || '',
      name: product.name || '',
      category: product.category?.name || '',
      supplier: product.supplier?.name || '',
      price: product.price
    };
  }

  // Save Edited Product
  saveEdit() {
    if (!this.auth.isLoggedIn()) {
      this.editMessage = 'Please log in first.';
      return;
    }

    if (
      !this.editProduct.name.trim() ||
      !this.editProduct.sku.trim() ||
      !this.editProduct.category.trim() ||
      !this.editProduct.supplier.trim() ||
      !Number.isFinite(Number(this.editProduct.price)) ||
      Number(this.editProduct.price) < 0
    ) {
      this.editMessage = 'Please enter valid product details.';
      return;
    }

    const data = {
      sku: this.editProduct.sku,
      name: this.editProduct.name,
      category: {
        name: this.editProduct.category
      },
      supplier: {
        name: this.editProduct.supplier
      },
      price: Number(this.editProduct.price)
    };

    this.savingEdit = true;

    this.http.put<any>(
      '/api/v1.0/products/' +
        encodeURIComponent(this.editingProductId),
      data,
      { headers: this.auth.getAuthHeaders() }
    ).subscribe({
      next: (updatedProduct) => {
        this.products = this.products.map(p =>
          p.product_id === this.editingProductId
            ? updatedProduct
            : p
        );

        this.searchProducts();
        this.editingProductId = '';
        this.editMessage = 'Product updated successfully!';
        this.savingEdit = false;

        this.cdr.markForCheck();
      },
      error: (error) => {
        this.editMessage =
          error.error?.error || 'Update failed.';

        this.savingEdit = false;
        this.cdr.markForCheck();
      }
    });
  }

  // Delete Product
  deleteProduct(product: any) {
    if (!confirm('Delete ' + product.name + '?')) {
      return;
    }

    this.deletingId = product.product_id;

    this.http.delete<any>(
      '/api/v1.0/products/' +
        encodeURIComponent(product.product_id),
      { headers: this.auth.getAuthHeaders() }
    ).subscribe({
      next: () => {
        this.products = this.products.filter(
          p => p.product_id !== product.product_id
        );

        this.searchProducts();

        this.editMessage = 'Product deleted successfully!';
        this.deletingId = '';

        this.cdr.markForCheck();
      },
      error: (error) => {
        this.editMessage =
          error.error?.error || 'Delete failed.';

        this.deletingId = '';
        this.cdr.markForCheck();
      }
    });
  }

  // Search all database products
  searchDatabase() {
    const term = this.searchTerm.trim();

    if (!term) {
      this.clearSearch();
      return;
    }

    this.errorMessage = '';
    this.isSearching = true;

    this.http.get<any>(
      '/api/v1.0/products/search',
      {
        params: { name: term },
        headers: this.auth.getAuthHeaders()
      }
    ).subscribe({
      next: (data) => {
        if (
          this.searchTerm.trim() !== term ||
          !this.isSearching
        ) {
          return;
        }

        this.filteredProducts = Array.isArray(data)
          ? data
          : data.products ?? [];

        this.cdr.markForCheck();
      },
      error: (error) => {
        if (
          this.searchTerm.trim() !== term ||
          !this.isSearching
        ) {
          return;
        }

        console.error('Search error:', error);
        this.errorMessage = 'Unable to search products.';

        this.cdr.markForCheck();
      }
    });
  }

  // Show All Products
  clearSearch() {
    this.searchTerm = '';
    this.isSearching = false;
    this.errorMessage = '';

    this.filteredProducts = [...this.products];

    if (this.products.length === 0) {
      this.loadProducts(1);
    } else {
      this.cdr.markForCheck();
    }
  }

  // Show Low Stock Products
  showLowStock() {
    this.searchTerm = '';
    this.errorMessage = '';
    this.isSearching = true;

    this.http.get<any>(
      '/api/v1.0/products/low-stock',
      { headers: this.auth.getAuthHeaders() }
    ).subscribe({
      next: (data) => {
        this.filteredProducts = Array.isArray(data)
          ? data
          : data.products ??
            data.low_stock_products ??
            [];

        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error(error);

        this.errorMessage =
          'Unable to load low stock products.';

        this.isSearching = false;
        this.cdr.markForCheck();
      }
    });
  }

  // Open Stock Update Form
  openStockForm(product: any) {
    this.selectedStockProduct = product;
    this.stockMessage = '';

    this.stockChange = {
      type: 'received',
      quantity: 1,
      warehouse:
        product.stock?.locations?.[0]?.warehouse || '',
      reason: ''
    };
  }

  // Save Stock Update
  saveStock() {
    const quantity = Number(this.stockChange.quantity);

    if (
      !this.selectedStockProduct ||
      !Number.isInteger(quantity) ||
      quantity <= 0 ||
      !this.stockChange.warehouse
    ) {
      this.stockMessage =
        'Please enter valid stock details.';
      return;
    }

    const product = this.selectedStockProduct;

    const data = {
      type: this.stockChange.type,
      quantity: quantity,
      warehouse: this.stockChange.warehouse,
      reason: this.stockChange.reason
    };

    this.stockSaving = true;
    this.stockMessage = '';

    this.http.put<any>(
      '/api/v1.0/products/' +
        encodeURIComponent(product.product_id) +
        '/stock',
      data,
      { headers: this.auth.getAuthHeaders() }
    ).subscribe({
      next: (result) => {
        const change =
          data.type === 'sold' ? -quantity : quantity;

        product.stock.quantity = result.new_quantity;

        const location = product.stock.locations?.find(
          (item: any) =>
            item.warehouse === data.warehouse
        );

        if (location) {
          location.quantity += change;
        }

        this.stockMessage = 'Stock updated successfully!';
        this.stockSaving = false;
        this.selectedStockProduct = null;

        this.cdr.markForCheck();
      },
      error: (error) => {
        this.stockMessage =
          error.error?.error ||
          'Unable to update stock.';

        this.stockSaving = false;
        this.cdr.markForCheck();
      }
    });
  }

  // View Stock History
  viewStockHistory(product: any) {
    this.selectedHistoryProduct = product.product_id;
    this.stockMovements = [];
    this.historyMessage = '';

    this.http.get<any>(
      '/api/v1.0/products/' +
        encodeURIComponent(product.product_id) +
        '/stock-movements?pn=1&ps=100',
      { headers: this.auth.getAuthHeaders() }
    ).subscribe({
      next: (data) => {
        this.stockMovements =
          data.stock_movements ?? [];

        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error(error);

        this.historyMessage =
          'Unable to load stock history.';

        this.cdr.markForCheck();
      }
    });
  }
}
