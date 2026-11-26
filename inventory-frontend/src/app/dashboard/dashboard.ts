
import { CommonModule } from '@angular/common';
import { Component, OnInit, ChangeDetectorRef, EventEmitter, Output } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { forkJoin } from 'rxjs';
import { Auth } from '../services/auth';

interface ChartBar {
  name: string;
  value: number;
  width: number;
}

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class Dashboard implements OnInit {
 @Output() stockProductClick = new EventEmitter<string>();

  totalProducts = 0;
  totalCategories = 0;
  totalSuppliers = 0;
  lowStockCount = 0;

  totalUnits = 0;
  totalStockValue = 0;
  totalCostValue = 0;
  hasCostData = false;
  outOfStockCount = 0;
  suppliersOnHold = 0;

  categoryChart: ChartBar[] = [];
  warehouseChart: ChartBar[] = [];

  lowStockProducts: any[] = [];
  recentMovements: any[] = [];

  // Sales by Supplier
  salesFromDate = '';
  salesToDate = '';
  salesBySupplier: any[] = [];
  salesRecords: any[] = [];

  // Batch expiry
  batchRecords: any[] = [];
  expiringBatches: any[] = [];
  expiryDays = '365';

  // Sales pagination
  salesPage = 1;
  salesPageSize = 6;

  get pagedSalesBySupplier() {
    const start = (this.salesPage - 1) * this.salesPageSize;

    return this.salesBySupplier.slice(
      start,
      start + this.salesPageSize
    );
  }

  get salesTotalPages() {
    return Math.max(
      1,
      Math.ceil(this.salesBySupplier.length / this.salesPageSize)
    );
  }

  previousSalesPage() {
    if (this.salesPage > 1) {
      this.salesPage--;
    }
  }

  nextSalesPage() {
    if (this.salesPage < this.salesTotalPages) {
      this.salesPage++;
    }
  }

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
        '/api/v1.0/categories',
        { headers }
      ),
      suppliers: this.http.get<any[]>(
        '/api/v1.0/suppliers',
        { headers }
      ),
      lowStock: this.http.get<any>(
        '/api/v1.0/products/low-stock',
        { headers }
      )
    }).subscribe({
      next: (data) => {
        this.totalCategories = data.categories.length;
        this.totalSuppliers = data.suppliers.length;

        const lowStock = data.lowStock;

        this.lowStockProducts = Array.isArray(lowStock)
          ? lowStock
          : lowStock.products ??
            lowStock.low_stock_products ??
            lowStock.low_stock ??
            lowStock.items ??
            [];

        this.lowStockCount =
          lowStock.count ?? this.lowStockProducts.length;

        this.suppliersOnHold = data.suppliers.filter(
          (supplier: any) =>
            ['hold', 'on hold', 'on_hold'].includes(
              String(supplier.status ?? '').toLowerCase()
            )
        ).length;

        this.loadProducts(1, []);
      },
      error: (error) => {
        console.error(error);
        this.errorMessage = 'Unable to load dashboard data.';
        this.loading = false;
        this.cdr.markForCheck();
      }
    });
  }

  loadProducts(page: number, allProducts: any[]) {
    this.http.get<any>(
      '/api/v1.0/products',
      {
        params: {
          pn: page.toString(),
          ps: '100'
        },
        headers: this.auth.getAuthHeaders()
      }
    ).subscribe({
      next: (data) => {
        const products = Array.isArray(data)
          ? data
          : data.products ?? [];

        const combined = [...allProducts, ...products];

        if (products.length === 100) {
          this.loadProducts(page + 1, combined);
        } else {
          this.calculateDashboard(combined);
          this.loading = false;
          this.cdr.markForCheck();
        }
      },
      error: (error) => {
        console.error(error);
        this.errorMessage = 'Unable to load products.';
        this.loading = false;
        this.cdr.markForCheck();
      }
    });
  }

  calculateDashboard(products: any[]) {
    this.totalProducts = products.length;
    this.totalUnits = 0;
    this.totalStockValue = 0;
    this.totalCostValue = 0;
    this.hasCostData = false;
    this.outOfStockCount = 0;

    const categoryCounts: Record<string, number> = {};
    const warehouseCounts: Record<string, number> = {};

    const warehouseNames: Record<string, string> = {
      'WH-MAIN': 'Leeds Main Warehouse',
      'WH-OVERFLOW': 'Leeds Overflow Store',
      'WH-SHOP': 'Trade Counter'
    };

    for (const product of products) {
      const stock = product.stock ?? {};
      const quantity = Number(stock.quantity ?? 0) || 0;

      const price = Number(
        product.price ?? product.pricing?.retail ?? 0
      ) || 0;

      this.totalUnits += quantity;
      this.totalStockValue += quantity * price;

      if (quantity === 0) {
        this.outOfStockCount++;
      }

      // Stock value at cost
      const costSource =
        product.supplier?.unit_cost ??
        product.cost_price ??
        product.purchase_price ??
        product.cost ??
        product.pricing?.cost;

      if (costSource !== undefined && costSource !== null) {
        const cost = Number(costSource);

        if (Number.isFinite(cost)) {
          this.totalCostValue += quantity * cost;
          this.hasCostData = true;
        }
      }

      // Products by category
      const category = typeof product.category === 'object'
        ? product.category?.name
        : product.category;

      const categoryName = String(
        category || 'Uncategorised'
      );

      categoryCounts[categoryName] =
        (categoryCounts[categoryName] || 0) + 1;

      // Stock by warehouse
      const locations = stock.locations;

      if (Array.isArray(locations)) {
        for (const location of locations) {
          const warehouseCode =
            typeof location.warehouse === 'string'
              ? location.warehouse
              : location.warehouse?.name ?? '';

          const warehouse = String(
            location.warehouse_name ??
            warehouseNames[warehouseCode] ??
            (warehouseCode || 'Unknown warehouse')
      );

          const amount = Number(
            location.quantity ?? location.qty ?? 0
          ) || 0;

          warehouseCounts[warehouse] =
            (warehouseCounts[warehouse] || 0) + amount;
        }
      } else if (locations && typeof locations === 'object') {
        for (const [code, value] of Object.entries(locations)) {
          const amount = Number(
            typeof value === 'object' && value !== null
              ? (value as any).quantity ??
                (value as any).qty ?? 0
              : value
          ) || 0;

          const warehouse = warehouseNames[code] ?? code;

          warehouseCounts[warehouse] =
            (warehouseCounts[warehouse] || 0) + amount;
        }
      }
    }

    // Dashboard graphs
    this.categoryChart = this.createChart(
      categoryCounts,
      6
    );

    this.warehouseChart = this.createChart(
      warehouseCounts,
      8
    );

    // Recent Stock Movements
    this.recentMovements = products.flatMap(product =>
      (product.stock_movements ?? []).map((movement: any) => ({
        product: product.name,
        type: movement.type,
        quantity: movement.quantity,
        date: movement.date?.$date ?? movement.date,
        by: movement.recorded_by?.name ?? 'Unknown'
      }))
    )
    .filter(movement => movement.date)
    .sort((a, b) =>
      new Date(b.date).getTime() -
      new Date(a.date).getTime()
    )
    .slice(0, 8);

    // Sales by Supplier
    this.salesRecords = products.flatMap(product =>
      (product.stock_movements ?? [])
        .filter((movement: any) =>
          movement.type === 'sold' &&
          movement.reference?.type === 'sales_order'
        )
        .map((movement: any, index: number) => ({
          supplier: product.supplier?.name ??
            (typeof product.supplier === 'string'
              ? product.supplier
              : 'Unknown supplier'),

          orderId: movement.reference?.number ??
            `${product.product_id}-${index}`,

          date: movement.date?.$date ??
            movement.date ?? '',

          quantity: Number(movement.quantity),

          unitPrice: Number(movement.unit_price)
        }))
        .filter((sale: any) =>
          sale.date &&
          Number.isFinite(sale.quantity) &&
          Number.isFinite(sale.unitPrice)
        )
    );

    this.updateSalesBySupplier();

    // Expiring batches
    this.batchRecords = products.flatMap(product =>
      (product.stock_movements ?? [])
        .filter((movement: any) =>
          movement.type === 'received' &&
          movement.batch?.number &&
          movement.batch?.expiry_date
        )
        .map((movement: any) => ({
          product: product.name,
          batchNumber: movement.batch.number,
          expiryDate:
            movement.batch.expiry_date?.$date ??
            movement.batch.expiry_date,
          receivedQty: Number(movement.quantity ?? 0)
        }))
    );

    this.updateExpiringBatches();
  }

  // Create horizontal bar graphs
  createChart(
    counts: Record<string, number>,
    limit: number
  ): ChartBar[] {
    const entries = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, limit);

    const maximum = Math.max(
      1,
      ...entries.map(item => item[1])
    );

    return entries.map(([name, value]) => ({
      name,
      value,
      width: (value / maximum) * 100
    }));
  }

  // Calculate Sales by Supplier
  updateSalesBySupplier() {
    this.salesPage = 1;

    const totals: Record<string, {
      supplier: string;
      orders: Set<string>;
      units: number;
      revenue: number;
    }> = {};

    const filtered = this.salesRecords.filter(sale => {
      const date = String(sale.date).slice(0, 10);

      return (
        (!this.salesFromDate || date >= this.salesFromDate) &&
        (!this.salesToDate || date <= this.salesToDate)
      );
    });

    for (const sale of filtered) {
      const name = sale.supplier;

      if (!totals[name]) {
        totals[name] = {
          supplier: name,
          orders: new Set<string>(),
          units: 0,
          revenue: 0
        };
      }

      totals[name].orders.add(String(sale.orderId));
      totals[name].units += sale.quantity;
      totals[name].revenue +=
        sale.quantity * sale.unitPrice;
    }

    this.salesBySupplier = Object.values(totals)
      .map(item => ({
        supplier: item.supplier,
        orders: item.orders.size,
        units: item.units,
        revenue: item.revenue
      }))
      .sort((a, b) => b.revenue - a.revenue);

    this.cdr.markForCheck();
  }

  // Filter expiring batches
  updateExpiringBatches() {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const endDate = new Date(today);
    endDate.setDate(
      endDate.getDate() + Number(this.expiryDays)
    );

    this.expiringBatches = this.batchRecords
      .filter(batch => {
        const expiry = new Date(batch.expiryDate);

        return (
          !Number.isNaN(expiry.getTime()) &&
          expiry >= today &&
          expiry <= endDate
        );
      })
      .sort((a, b) =>
        new Date(a.expiryDate).getTime() -
        new Date(b.expiryDate).getTime()
      );

    this.cdr.markForCheck();
  }
}
