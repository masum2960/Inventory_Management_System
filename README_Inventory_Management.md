# Inventory Management System API

A RESTful backend API built with **Flask** and **MongoDB** to manage products, categories, suppliers, users, and inventory stock. The aim of this project is to make everyday inventory operations easier to organise and track, from adding a product to recording stock movements and identifying items that need restocking.

This project was developed for **COM661 – Full-Stack Strategies and Development (CW1)** at Ulster University.

- **Local base URL:** `http://127.0.0.1:5001/api/v1.0`
- **Database:** `inventory_management`
- **Latest recorded Postman run:** 26 requests, **30 passing assertions, 0 failures** (3 requests returned HTTP 200 but did not have test assertions)

---

## Table of contents

1. [Features](#features)
2. [Tech stack](#tech-stack)
3. [Project structure](#project-structure)
4. [Getting started](#getting-started)
5. [Sample dataset](#sample-dataset)
6. [Authentication and roles](#authentication-and-roles)
7. [Business rules](#business-rules)
8. [API reference](#api-reference)
9. [Data model](#data-model)
10. [Error handling](#error-handling)
11. [Testing](#testing)
12. [Project notes](#project-notes)

---

## Features

**Product management**
- View all products or retrieve an individual product by ID
- Add, update and delete products
- Search products by name, category or status
- Identify products whose available quantity is at or below their minimum stock level
- Record stock changes and review movement history

**Categories and suppliers**
- Browse individual categories and suppliers
- Add, edit and remove category and supplier records
- Keep related inventory information organised

**Users and authentication**
- Register a new staff account and log in using HTTP Basic Authentication
- Receive a JSON Web Token (JWT) after a successful login
- Log out by revoking the current token
- Allow administrators to view, update and delete user records, with restrictions

**Platform**
- REST-style endpoints and JSON responses
- Role-based permissions for sensitive operations
- MongoDB persistence through PyMongo
- Automated API testing with Postman

---

## Tech stack

| Area | Technology |
|---|---|
| Programming language | Python 3 |
| Backend framework | Flask |
| Database | MongoDB |
| Database driver | PyMongo |
| Authentication | HTTP Basic Authentication and JWT (PyJWT, HS256) |
| Password hashing | Werkzeug |
| Configuration | python-dotenv |
| API testing | Postman |
| Development tools | VS Code, MongoDB Compass, Git and GitHub |

---

## Project structure

```text
Inventory_Management_System/
├── app.py                    # Flask application and blueprint registration
├── config.py                 # Reads the SECRET_KEY from the environment
├── extensions.py             # MongoDB connection and collection references
├── decorators.py             # Basic/Bearer authentication and role checks
├── helpers.py                # Shared helper functions
├── import_data.py            # Imports the sample JSON datasets
├── generate_hash.py          # Password-hashing helper script
├── requirements.txt          # Python dependencies
├── .env.example              # Example configuration (create this locally)
├── .gitignore
├── blueprints/
│   ├── __init__.py
│   ├── auth.py               # Register, login and logout
│   ├── products.py           # Product CRUD, stock and search
│   ├── categories.py         # Category CRUD
│   ├── suppliers.py          # Supplier CRUD
│   └── users.py              # Admin user operations
├── inventory_datasets/
│   ├── products.json
│   ├── categories.json
│   ├── suppliers.json
│   └── users.json
└── README.md
```

> **Note:** `.env.example` is a recommended file to add; it was not included in the uploaded project ZIP. The real `.env` should remain on your local machine and should not be committed to GitHub.

---

## Getting started

### Requirements

- Python 3 with `pip`
- MongoDB running locally on `mongodb://localhost:27017`
- Postman for testing the endpoints
- MongoDB Compass (optional, for viewing collections)

### Installation

Download or clone the project, then open its root folder in a terminal.

```bash
python -m venv .venv
```

Activate the environment on **Windows PowerShell**:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root and add a long, random secret:

```dotenv
SECRET_KEY=replace_this_with_a_long_random_secret
```

The app reads `SECRET_KEY` from this file. The MongoDB connection is currently configured in `extensions.py` as `mongodb://localhost:27017`.

### Load the sample data

Make sure the MongoDB server is running, then execute:

```bash
python import_data.py
```

The script reads the four JSON files in `inventory_datasets/` and imports them into the `inventory_management` database. It checks record identifiers and handles existing records, so review the script before using it to refresh a database that contains work you want to keep.

### Run the API

```bash
python app.py
```

The server starts at `http://127.0.0.1:5001`. Opening that address in a browser displays the welcome page. The API routes use the `/api/v1.0` prefix.

---

## Sample dataset

The supplied dataset contains **100 records in each of the four main collections**.

| Collection | Records | Main purpose |
|---|---:|---|
| `products` | 100 | Product details, pricing, stock levels and movement history |
| `categories` | 100 | Product categories and subcategories |
| `suppliers` | 100 | Supplier contact information and business details |
| `users` | 100 | Staff/admin accounts, roles and stored password hashes |

The database also uses a `token_blocklist` collection to record revoked JWTs. Stock movements are embedded in product documents rather than stored in a separate MongoDB collection.

The sample data is for development and demonstration. User password hashes should not be published in a public repository as production credentials.

---

## Authentication and roles

1. **Register:** `POST /register` creates a new account with the `staff` role. Required fields: `user_id`, `name`, `email`, `password` (at least 8 characters).
2. **Login:** `POST /login` accepts HTTP Basic Authentication (`user_id` and password) or a JSON body containing those fields. A successful login returns a JWT valid for **one hour**.
3. **Authorise requests:** Protected endpoints accept HTTP Basic Authentication or a JWT sent as `Authorization: Bearer <token>`.
4. **Logout:** `POST /logout` requires authentication and revokes the JWT. For JWT logout, use the Bearer token returned by login.

| Role | Typical permissions |
|---|---|
| Public / unauthenticated | Read public category/supplier information and applicable product routes; register and log in |
| `staff` | Access permitted stock operations and low-stock/movement views |
| `admin` | Create/update/delete products, categories and suppliers; manage user records |

Permissions vary by endpoint. Some GET routes are public, while `GET /products` is protected. See the API reference and the route decorators in the source code for the precise rules.

---

## Business rules

**Products and stock**
- Product records use a `product_id` to identify individual items.
- Stock updates are handled through a dedicated endpoint, rather than changing stock quantities through an unrelated operation.
- Stock movement history can be filtered by movement type and paginated with `pn` and `ps`.
- The low-stock endpoint selects products where `stock.quantity` is less than or equal to `stock.min_level`.
- Product search supports `name`, `category` and `status` query parameters.

**Categories and suppliers**
- New categories require `category_id` and `name`.
- New suppliers require `supplier_id` and `name`.
- Duplicate IDs return a conflict response rather than silently creating a second record.
- Only administrators may create, edit or delete categories and suppliers.

**Users**
- New registrations receive the `staff` role.
- Administrators can update a user's `name` and `email` through the user update route.
- The user update route checks for duplicate email addresses.
- Administrators cannot delete their own account through the user deletion route.
- User list/detail responses omit password hashes.

---

## API reference

All paths below are relative to **`/api/v1.0`**. Many write endpoints accept JSON or `x-www-form-urlencoded` form data. Nested product fields may need JSON to preserve their structure.

### Authentication

| Method | Path | Purpose | Successful status |
|---|---|---|---|
| POST | `/register` | Create a staff account | `201` |
| POST | `/login` | Authenticate and return a JWT | `200` |
| POST | `/logout` | Revoke the current JWT | `200` |

### Products

| Method | Path | Purpose | Successful status |
|---|---|---|---|
| GET | `/products` | List products | `200` |
| GET | `/products/<product_id>` | View one product | `200` |
| POST | `/products` | Create a product (admin) | `201` |
| PUT | `/products/<product_id>` | Update a product (admin) | `200` |
| DELETE | `/products/<product_id>` | Delete a product (admin) | `200` |
| PUT | `/products/<product_id>/stock` | Update stock (admin/staff) | `200` |
| GET | `/products/low-stock` | Find products needing restock (admin/staff) | `200` |
| GET | `/products/<product_id>/stock-movements` | View stock movement history (admin/staff) | `200` |
| GET | `/products/search?name=&category=&status=` | Search/filter products | `200` |

### Categories

| Method | Path | Purpose | Successful status |
|---|---|---|---|
| GET | `/categories` | List categories | `200` |
| GET | `/categories/<category_id>` | View a category | `200` |
| POST | `/categories` | Create a category (admin) | `201` |
| PUT | `/categories/<category_id>` | Update a category (admin) | `200` |
| DELETE | `/categories/<category_id>` | Delete a category (admin) | `200` |

### Suppliers

| Method | Path | Purpose | Successful status |
|---|---|---|---|
| GET | `/suppliers` | List suppliers | `200` |
| GET | `/suppliers/<supplier_id>` | View a supplier | `200` |
| POST | `/suppliers` | Create a supplier (admin) | `201` |
| PUT | `/suppliers/<supplier_id>` | Update a supplier (admin) | `200` |
| DELETE | `/suppliers/<supplier_id>` | Delete a supplier (admin) | `200` |

### Users

| Method | Path | Purpose | Successful status |
|---|---|---|---|
| GET | `/users` | List users (admin) | `200` |
| GET | `/users/<user_id>` | View a user (admin) | `200` |
| PUT | `/users/<user_id>` | Update name/email (admin) | `200` |
| DELETE | `/users/<user_id>` | Delete a user (admin) | `200` |

---

## Data model

MongoDB database: **`inventory_management`**.

The following examples show the general shape of the documents. They are simplified, not complete copies of the supplied dataset.

**`products`**

```json
{
  "product_id": "P001",
  "sku": "example-sku",
  "name": "Example product",
  "category": { "name": "Example category" },
  "stock": { "quantity": 20, "min_level": 5 },
  "stock_movements": []
}
```

**`categories`**

```json
{
  "category_id": "C01",
  "name": "Example category",
  "slug": "example-category",
  "subcategories": []
}
```

**`suppliers`**

```json
{
  "supplier_id": "SUP01",
  "name": "Example supplier",
  "email": "supplier@example.com",
  "status": "active"
}
```

**`users`**

```json
{
  "user_id": "U001",
  "name": "Example user",
  "email": "user@example.com",
  "role": "admin",
  "password_hash": "<stored password hash>"
}
```

**`token_blocklist`** stores identifiers of JWTs that have been logged out. A MongoDB TTL index on `expires_at` removes expired revocation records automatically.

---

## Error handling

The API returns JSON error messages for common validation and access problems.

| HTTP status | Meaning |
|---|---|
| `400` | Missing or invalid request data |
| `401` | Missing, invalid or expired authentication |
| `403` | Authenticated user lacks the required role |
| `404` | Requested record does not exist |
| `409` | Conflict, such as an already-used ID or email address |

Example:

```json
{
  "error": "Product not found"
}
```

The exact error text depends on the endpoint.

---

## Testing

The API was tested locally using the **COM661 Inventory Management API** Postman collection and its Collection Runner.

**Latest recorded run — 3 November 2026**

| Result | Value |
|---|---:|
| Requests executed | 26 |
| Automated assertions passed | **30** |
| Automated assertions failed | **0** |
| Run status | Finished |

The run covered registration, login, logout, product operations, stock updates and history, categories, suppliers, and user management. All 26 requests received successful HTTP response codes.

**Testing note:** The `Search Products`, `Update User` and `Delete User` requests returned HTTP `200`, but their exported results contain no Postman test assertions. Therefore, **30 passed** describes the assertions that actually ran, not a claim of complete test coverage.

### Running the Postman tests

1. Start MongoDB and run `python app.py`.
2. Open the saved **COM661 Inventory Management API** collection in Postman.
3. Confirm request URLs point to `http://127.0.0.1:5001`.
4. Check the Basic Auth credentials used by the collection and ensure that the test registration ID is not already present in MongoDB.
5. Run the collection in its saved order, keeping **Logout last**.
6. Review the Collection Runner summary and export the run results if required.

The tests create, update and delete records. Repeated runs may need a new registration ID or a clean test database to avoid duplicate-record errors. Do not run destructive test requests against production data.

---

## Project notes

This is a backend coursework project. It focuses on API design, database operations, authentication and testing; a separate frontend is not included in this submission.

The project helped me practise organising Flask routes into blueprints, working with MongoDB documents, applying role-based permissions and checking API behaviour through Postman. The next stage would be to connect a frontend interface to the API and improve test coverage, particularly around invalid inputs and access restrictions.

---

*COM661 – Full-Stack Strategies and Development | Inventory Management System API*
