"""
Development settings for chat_app project.
Use this for development environment.
"""

from .settings import *

# Development-specific settings
DEBUG = True

# Generate a new secret key for development
SECRET_KEY = 'z2k&eP!V-Xl&6M^(3dHNX#2Bii&TdXGiXX)g78p=Qt1fdS&kj^' 

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Use console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development database (already configured for SQLite)
# No changes needed for DATABASES

# Optional: Add django-debug-toolbar for development
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

print("Development mode: DEBUG = True")
