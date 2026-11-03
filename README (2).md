# Inventory Management System — COM661 CW1

A Flask REST API backed by MongoDB for managing products, stock movements, categories, suppliers and users. This project is intended to run locally for coursework demonstration and testing.

## Requirements

- Python 3
- MongoDB Community Server running locally on port 27017
- Postman for API testing

Python packages are listed in `requirements.txt`.

## Setup (Windows PowerShell)

Open a terminal in the project folder, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file in the project root with your own long, random secret key:

```dotenv
SECRET_KEY=replace-with-your-own-long-random-secret
```

**Do not commit or share your real `.env` file.** Ensure MongoDB is running at `mongodb://localhost:27017`.

## Import the dataset

The supplied JSON datasets are in `inventory_datasets/`. The import script loads `products`, `categories`, `suppliers` and `users` into the `inventory_management` database.

```powershell
python import_data.py
```

**Important:** The import script checks for records not present in its dataset and can refuse to import into a database containing extra test records. Back up your existing database before resetting or cleaning test data.

## Start the API

```powershell
python app.py
```

The local server runs at `http://127.0.0.1:5001`. Open that address to see the welcome message. API endpoints use the prefix `/api/v1.0`.

## API features

- Authentication: register, login and logout
- Products: list, search, retrieve, create, update and delete; low-stock lookup, stock updates and stock movement history
- Categories: list, retrieve, create, update and delete
- Suppliers: list, retrieve, create, update and delete
- Users: list, retrieve, update and delete (role-restricted)

## Authentication and testing

Use Postman to send requests to the local API. Login is `POST /api/v1.0/login` and accepts HTTP Basic authentication using a valid dataset user's credentials, or JSON credentials. Successful login returns a JWT. Logout is `POST /api/v1.0/logout` and requires the JWT as a Bearer token.

Other protected endpoints use the authentication and role requirements implemented in `decorators.py`. Use the Postman collection's configured authentication for each request. Do not include passwords or live tokens in submitted documentation.

The automated Postman collection run supplied separately records **26 requests executed, 30 assertions passed and 0 failed** (3 requests returned successful HTTP responses but had no assertions).

## Project files

- `app.py` — Flask application and blueprint registration
- `config.py` — configuration and required secret key
- `extensions.py` — MongoDB connection and collections
- `decorators.py` — authentication and role checks
- `helpers.py` — response helpers
- `blueprints/` — route handlers for authentication, products, categories, suppliers and users
- `import_data.py` — imports supplied JSON datasets into MongoDB
- `generate_hash.py` — password-hash utility
- `inventory_datasets/` — original JSON datasets
- `requirements.txt` — Python dependencies

## Submission and security notes

Include source code and this README in the backend ZIP, but exclude `.env`, `.git/`, `.venv/`, `__pycache__/` and local temporary files. Submit the required database export, code listing, endpoint summary, Postman test results, Postman-generated API documentation, self-evaluation and demonstration material according to the coursework instructions. Database exports containing user password hashes should only be submitted through the approved private coursework channel.
