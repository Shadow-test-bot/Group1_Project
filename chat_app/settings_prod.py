"""
Production settings for chat_app project.
IMPORTANT: Update the values marked with TODO before deploying!
"""

from .settings import *

# SECURITY WARNING: Generate a new secret key for production!
# TODO: Replace with a new secret key
SECRET_KEY = os.environ.get('SECRET_KEY', 'hHG5ZUcVoOcXLoka2K*QwU7Ftuu!Qd2q^Os7!ULda0C#-i2Y2$')

# SECURITY WARNING: Don't run with debug turned on in production!
DEBUG = False

# TODO: Update with your actual domain names
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Security settings for production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Use Redis for channel layers in production
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Production database (if not using SQLite)
# TODO: Configure your production database
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'DB_ChatApp',
        'USER': 'sa',
        'PASSWORD': '111222333',
        'HOST': 'DESKTOP-3VI1B1T\\SQLEXPRESS',  # e.g., 'localhost\\SQLEXPRESS'
        'PORT': '',  # Default MSSQL port is 1433; leave blank if using named instance
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',  # Or 18 depending on your version
        },
    }
}


# Production email settings
# TODO: Configure your email backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'bobunhak594@gmail.com'
EMAIL_HOST_PASSWORD = 'tsnd nvdn npyp oecs'
DEFAULT_FROM_EMAIL = 'Chat_App Support <Hak@gmail.com>'

# Static files for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Logging for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

print("Production mode: DEBUG = False")
