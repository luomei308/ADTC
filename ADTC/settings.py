"""Configuration for the ADTC web application.

All deployment-specific values are read from environment variables so that
no credentials or machine-specific paths are stored in the repository.
See `.env.example` for the full list.
"""
import os
import secrets

DEBUG = os.environ.get("ADTC_DEBUG", "false").lower() in ("1", "true", "yes")

# Flask secret key. Set ADTC_SECRET_KEY in production; a random key is
# generated otherwise (sessions will not survive a restart).
SECRET_KEY = os.environ.get("ADTC_SECRET_KEY") or secrets.token_hex(32)

# MongoDB connection, e.g. mongodb://user:password@127.0.0.1:27017/ADTC
MONGO_URI = os.environ.get("ADTC_MONGO_URI", "mongodb://127.0.0.1:27017/ADTC")

# Path to the Rscript executable used to draw survival curves.
RSCRIPT = os.environ.get("ADTC_RSCRIPT", "Rscript")

# Directory holding the per-cancer <CANCER>.<TYPE>.RData files.
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("ADTC_DATA_DIR", os.path.join(_BASE_DIR, "static", "ADTC", "data"))
