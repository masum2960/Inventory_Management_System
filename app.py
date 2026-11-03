
from dotenv import load_dotenv

# Load environment variables before importing other project modules
load_dotenv()

from flask import Flask, make_response
from config import SECRET_KEY

from blueprints.auth import auth_bp
from blueprints.products import products_bp
from blueprints.categories import categories_bp
from blueprints.suppliers import suppliers_bp
from blueprints.users import users_bp


app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY


@app.route("/", methods=["GET"])
def index():
    return make_response(
        "<h1>Welcome to the Inventory Management API</h1>",
        200
    )


# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(suppliers_bp)
app.register_blueprint(users_bp)


if __name__ == "__main__":
    app.run(
        debug=True,
        use_reloader=False,
        port=5001
    )
