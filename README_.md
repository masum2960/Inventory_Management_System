<div align="center">

# 📦 Inventory Management System

### A REST API for keeping inventory organised

**COM661 · Full-Stack Strategies and Development · Coursework 1**

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white) ![Flask](https://img.shields.io/badge/Flask-REST%20API-111827?logo=flask&logoColor=white) ![MongoDB](https://img.shields.io/badge/MongoDB-Database-47A248?logo=mongodb&logoColor=white) ![Postman](https://img.shields.io/badge/Postman-API%20Testing-FF6C37?logo=postman&logoColor=white)

*A backend project built to manage products, categories, suppliers, users and day-to-day stock changes in one place.*

</div>

---

## 👋 About the project

Keeping track of stock can get confusing when product details, supplier information and stock updates are stored separately. I built this **Inventory Management System** to bring those tasks together through a simple, structured API.

The project focuses on the **backend**: Flask handles the API requests, MongoDB stores the data, and Postman is used to test the endpoints. It was developed as part of my COM661 coursework.

## ✨ What it can do

| Area | Features |
| :-- | :-- |
| 🔐 **Authentication** | Register, log in, log out, and use JWT-based logout |
| 📦 **Products** | Add, view, search, update and delete products |
| 📉 **Stock** | Check low-stock products, update quantities and view stock movements |
| 🗂️ **Categories** | Organise products using category records |
| 🚚 **Suppliers** | Manage supplier information |
| 👤 **Users** | View and manage user records with role-based restrictions |

## 🛠️ Built with

- **Python & Flask** — API routes and request handling
- **MongoDB & PyMongo** — database storage and queries
- **JWT** — token-based authentication for logout
- **Postman** — manual requests and automated API tests
- **Git & GitHub** — version control

## 🚀 Getting started

The following instructions are for **Windows PowerShell**, which is the environment I used while developing the project.

### 1. Prerequisites

Make sure you have **Python 3**, **MongoDB Community Server**, and **Postman** installed. MongoDB should be running locally at `mongodb://localhost:27017`.

### 2. Install the Python dependencies

Open the project folder in VS Code and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure the secret key

Create a file named `.env` in the main project folder:

```dotenv
SECRET_KEY=replace-with-your-own-long-random-secret-key
```

> 🔒 **Security note:** Keep your real `.env` file private. Do not upload it to GitHub. The example above is a placeholder, not a real secret.

### 4. Import the sample data

With MongoDB running, use:

```powershell
python import_data.py
```

The script imports the JSON files from `inventory_datasets/` into the **`inventory_management`** database, using the `products`, `categories`, `suppliers` and `users` collections.

> **Already have data in MongoDB?** The import script can stop if it finds records that are not part of the supplied dataset. Back up your database before making changes or cleaning up test records.

### 5. Run the application

```powershell
python app.py
```

The API will be available at:

**`http://127.0.0.1:5001`**

You can open this address in a browser to see the welcome message. API routes begin with **`/api/v1.0`**.

## 🧪 Testing with Postman

I used Postman to test the API, including creating, retrieving, updating and deleting records.

For the tested setup:

1. Use **Register** or log in with an existing dataset account.
2. For **Login**, use the credentials of a valid account with the authentication format configured in Postman.
3. Use the appropriate authentication and role for protected requests.
4. Run the requests in order, leaving **Logout** until the end.

The saved Collection Runner export recorded:

| Result | Count |
| :-- | --: |
| Requests executed | **26** |
| Automated assertions passed | **30** |
| Automated assertions failed | **0** |

*These numbers describe one saved test run, not a guarantee that every possible input or error case has been tested. Three successful requests did not contain automated assertions.*

## 🗂️ Project structure

```text
Inventory_Management_System/
│
├── app.py                    # Flask app and blueprint registration
├── config.py                 # Application configuration
├── extensions.py             # MongoDB connection and collections
├── decorators.py             # Authentication and access control
├── helpers.py                # Shared helper functions
├── import_data.py            # Import sample JSON data
├── generate_hash.py          # Password hashing utility
├── requirements.txt          # Python dependencies
├── README.md                 # Project guide
│
├── blueprints/
│   ├── auth.py               # Register, login and logout
│   ├── products.py           # Product and stock endpoints
│   ├── categories.py         # Category endpoints
│   ├── suppliers.py          # Supplier endpoints
│   └── users.py              # User endpoints
│
└── inventory_datasets/
    ├── products.json
    ├── categories.json
    ├── suppliers.json
    └── users.json
```

## 🔗 Example API routes

| Method | Endpoint | Purpose |
| :-- | :-- | :-- |
| `POST` | `/api/v1.0/register` | Register a user |
| `POST` | `/api/v1.0/login` | Log in |
| `POST` | `/api/v1.0/logout` | Log out |
| `GET` | `/api/v1.0/products` | List or search products |
| `GET` | `/api/v1.0/products/low-stock` | Find low-stock products |
| `GET` | `/api/v1.0/products/P001` | Retrieve a product |
| `GET` | `/api/v1.0/categories` | List categories |
| `GET` | `/api/v1.0/suppliers` | List suppliers |
| `GET` | `/api/v1.0/users` | List users (admin role) |

This is a quick overview, not the full endpoint reference. The full routes are implemented in the `blueprints/` folder.

## 📌 A few things I learned

Working on this project gave me practical experience with structuring a Flask application using blueprints, connecting Python to MongoDB, handling API requests and responses, and checking API behaviour with Postman. Testing create–update–delete workflows also helped me understand why the order of requests matters.

## 🔒 Repository notes

- Keep `.env`, virtual environments, Python cache files and `.git/` out of the **coursework submission ZIP**.
- Keep `.git/` on your own computer so GitHub version control continues to work.
- Never publish real passwords, JWTs, secret keys or private database exports.
- The application runs in local **debug mode** for coursework development; it is not configured as a production deployment.

---

<div align="center">

**Made for COM661 Coursework 1**  
*Learning full-stack development, one API endpoint at a time.*

</div>
