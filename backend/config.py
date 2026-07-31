import os

# Port and host settings
PORT = int(os.environ.get("PORT", 8080))
HOST = os.environ.get("HOST", "127.0.0.1")

# JWT configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "projectlens-super-secret-key-1893")
JWT_ALGORITHM = "HS256"

# Live Gemini API Key loading
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Load from .env file if it exists locally for easier development/testing
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if key == "GEMINI_API_KEY":
                    GEMINI_API_KEY = val
                elif key == "JWT_SECRET":
                    JWT_SECRET = val
                elif key == "PORT":
                    PORT = int(val)
                elif key == "HOST":
                    HOST = val
