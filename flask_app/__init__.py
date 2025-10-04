"""
Flask application initialization and configuration.
Sets up the Flask app, configuration, template filters, and imports all route modules.
"""

from flask import Flask

from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')

# Initialize Flask application
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Development settings to prevent browser caching and enable auto-reload
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True


# Import database setup
# from database import database_setup

# Import all route modules
from . import routes
from . import politician_routes