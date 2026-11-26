
import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { Auth } from '../services/auth';

@Component({
  selector: 'app-categories',
  imports: [FormsModule],
  templateUrl: './categories.html',
  styleUrl: './categories.css'
})
export class Categories implements OnInit {

  categories: any[] = [];
  filteredCategories: any[] = [];
  searchTerm = '';
  errorMessage = '';
  message = '';

  showForm = false;
  editingId = '';
  saving = false;
  deletingId = '';

  formData = {
    category_id: '',
    name: '',
    slug: '',
    description: ''
  };

  pageNumber = 1;
pageSize = 10;

get pagedCategories() {
  const start = (this.pageNumber - 1) * this.pageSize;
  return this.filteredCategories.slice(start, start + this.pageSize);
}

nextPage() {
  if (this.pageNumber * this.pageSize < this.filteredCategories.length) {
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
    this.loadCategories();
  }

  loadCategories() {
    this.http.get<any[]>('/api/v1.0/categories', {
      headers: this.auth.getAuthHeaders()}).subscribe({
      next: (data) => {
        this.categories = data;
        this.searchCategories();
        this.cdr.markForCheck();
      },
      error: (error) => {
        console.error(error);
        this.errorMessage = 'Unable to load categories.';
        this.cdr.markForCheck();
      }
    });
  }

  searchCategories() {
    const term = this.searchTerm.toLowerCase().trim();

    this.filteredCategories = this.categories.filter(category =>
      category.name?.toLowerCase().includes(term)
    );
    this.pageNumber = 1;
  }

  addCategory() {
    this.editingId = '';
    this.showForm = true;
    this.message = '';

    this.formData = {
      category_id: '',
      name: '',
      slug: '',
      description: ''
    };
  }

  editCategory(category: any) {
    this.editingId = category.category_id;
    this.showForm = true;
    this.message = '';

    this.formData = {
      category_id: category.category_id,
      name: category.name || '',
      slug: category.slug || '',
      description: category.description || ''
    };
  }

  saveCategory() {
    if (!this.formData.category_id.trim() ||
        !this.formData.name.trim()) {
      this.message = 'Category ID and Name are required.';
      return;
    }

    const data = {
      category_id: this.formData.category_id.trim(),
      name: this.formData.name.trim(),
      slug: this.formData.slug.trim(),
      description: this.formData.description.trim()
    };

    const url = this.editingId
      ? '/api/v1.0/categories/' + encodeURIComponent(this.editingId)
      : '/api/v1.0/categories';

    this.saving = true;

    const request = this.editingId
      ? this.http.put(url, data, {
          headers: this.auth.getAuthHeaders()
        })
      : this.http.post(url, data, {
          headers: this.auth.getAuthHeaders()
        });

    request.subscribe({
      next: () => {
        this.message = this.editingId
          ? 'Category updated successfully!'
          : 'Category added successfully!';

        this.saving = false;
        this.showForm = false;
        this.editingId = '';
        this.loadCategories();
        this.cdr.markForCheck();
      },
      error: (error) => {
        this.message = error.error?.error || 'Unable to save category.';
        this.saving = false;
        this.cdr.markForCheck();
      }
    });
  }

  deleteCategory(category: any) {
    if (!confirm('Delete ' + category.name + '?')) return;

    this.deletingId = category.category_id;

    this.http.delete(
      '/api/v1.0/categories/' +
        encodeURIComponent(category.category_id),
      { headers: this.auth.getAuthHeaders() }
    ).subscribe({
      next: () => {
        this.message = 'Category deleted successfully!';
        this.deletingId = '';
        this.loadCategories();
        this.cdr.markForCheck();
      },
      error: (error) => {
        this.message = error.error?.error || 'Unable to delete category.';
        this.deletingId = '';
        this.cdr.markForCheck();
      }
    });
  }
}
