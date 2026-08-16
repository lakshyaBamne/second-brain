import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DBNAME = os.environ.get("MONGO_DBNAME", "second_brain")

    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
    # Set SESSION_COOKIE_SECURE=true in production (anywhere served over HTTPS,
    # e.g. Render) - kept off by default so local http://127.0.0.1 dev still works.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
