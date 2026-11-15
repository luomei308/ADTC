from flask_pymongo import PyMongo

from ADTC import app

# MONGO_URI is configured in ADTC/settings.py (env var ADTC_MONGO_URI).
mongo = PyMongo(app)
