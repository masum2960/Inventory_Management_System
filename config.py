
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing. Please set it in your .env file."
    )
