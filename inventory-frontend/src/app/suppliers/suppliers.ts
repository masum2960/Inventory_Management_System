
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { Auth } from '../services/auth';

@Component({
  selector: 'app-suppliers',
  imports: [FormsModule],
  templateUrl: './suppliers.html',
  styleUrl: './suppliers.css'
})
export class Suppliers implements OnInit {
  suppliers: any[] = [];
  filteredSuppliers: any[] = [];
  searchTerm = '';
  errorMessage = '';
  message = '';

  showForm = false;
  editingId = '';
  saving = false;
  deletingId = '';

  formData = {
    supplier_id: '',
    name: '',
    email: '',
    phone: '',
    status: 'active'
  };

  
pageNumber = 1;
pageSize = 10;

get pagedSuppliers() {
  const start = (this.pageNumber - 1) * this.pageSize;
  return this.filteredSuppliers.slice(start, start + this.pageSize);
}

nextPage() {
  if (this.pageNumber * this.pageSize < this.filteredSuppliers.length) {
    this.pageNumber++;
  }
}

previousPage() {
  if (this.pageNumber > 1) {
    this.pageNumber--;
  }
}


  constructor(
    private http: HttpClient,
    public auth: Auth,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.loadSuppliers();
  }

  loadSuppliers() {
    this.http.get<any[]>('/api/v1.0/suppliers', {
     headers: this.auth.getAuthHeaders()
    }).subscribe({

      next: (data) => {
        this.suppliers = data;
        this.searchSuppliers();
        this.errorMessage = '';
        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error(error);
        this.errorMessage = 'Unable to load suppliers.';
        this.cdr.markForCheck();
      }
    });
  }

  searchSuppliers() {
    const term = this.searchTerm.toLowerCase().trim();
    this.filteredSuppliers = this.suppliers.filter(supplier =>
      (supplier.name || '').toLowerCase().includes(term)
    );
    this.pageNumber = 1;
  }

  addSupplier() {
    this.editingId = '';
    this.showForm = true;
    this.message = '';
    this.formData = {
      supplier_id: '',
      name: '',
      email: '',
      phone: '',
      status: 'active'
    };
  }

  editSupplier(supplier: any) {
    this.editingId = supplier.supplier_id;
    this.showForm = true;
    this.message = '';

    this.formData = {
      supplier_id: supplier.supplier_id,
      name: supplier.name || '',
      email: supplier.email || '',
      phone: supplier.phone || '',
      status: supplier.status || 'active'
    };
  }

  saveSupplier() {
    if (!this.formData.supplier_id.trim() ||
        !this.formData.name.trim()) {
      this.message = 'Supplier ID and Name are required.';
      return;
    }

    const data = {
      name: this.formData.name.trim(),
      email: this.formData.email.trim(),
      phone: this.formData.phone.trim(),
      status: this.formData.status.trim()
    };

    this.saving = true;
    this.message = '';

    const request = this.editingId
      ? this.http.put(
          '/api/v1.0/suppliers/' +
            encodeURIComponent(this.editingId),
          data,
          { headers: this.auth.getAuthHeaders() }
        )
      : this.http.post(
          '/api/v1.0/suppliers',
          { supplier_id: this.formData.supplier_id.trim(), ...data },
          { headers: this.auth.getAuthHeaders() }
        );

    request.subscribe({
      next: () => {
        this.message = this.editingId
          ? 'Supplier updated successfully!'
          : 'Supplier added successfully!';

        this.saving = false;
        this.showForm = false;
        this.editingId = '';
        this.loadSuppliers();
        this.cdr.markForCheck();
      },
      error: (error) => {
        this.message = error.error?.error || 'Unable to save supplier.';
        this.saving = false;
        this.cdr.markForCheck();
      }
    });
  }

  deleteSupplier(supplier: any) {
    if (!confirm('Delete ' + supplier.name + '?')) return;

    this.deletingId = supplier.supplier_id;

    this.http.delete(
      '/api/v1.0/suppliers/' +
        encodeURIComponent(supplier.supplier_id),
      { headers: this.auth.getAuthHeaders() }
    ).subscribe({
      next: () => {
        this.message = 'Supplier deleted successfully!';
        this.deletingId = '';
        this.loadSuppliers();
        this.cdr.markForCheck();
      },
      error: (error) => {
        this.message = error.error?.error || 'Unable to delete supplier.';
        this.deletingId = '';
        this.cdr.markForCheck();
      }
    });
  }
}
