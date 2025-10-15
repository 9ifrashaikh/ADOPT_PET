import os
from datetime import timedelta

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'shunna@1234'
    BCRYPT_LOG_ROUNDS = 12  # For password hashing strength
    
    # Database configuration
    DB_HOST = os.environ.get('DB_HOST') or "localhost"
    DB_USER = os.environ.get('DB_USER') or "root"
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or "ifra@1234"
    DB_NAME = os.environ.get('DB_NAME') or "project"
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-super-secret-jwt-key-change-this-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 🔥🔥🔥 JWT COOKIE SUPPORT - THIS WAS MISSING! 🔥🔥🔥
    JWT_TOKEN_LOCATION = ['headers', 'cookies']  # Check BOTH headers AND cookies
    JWT_COOKIE_SECURE = False  # Set to True in production with HTTPS
    JWT_COOKIE_CSRF_PROTECT = False  # Disable CSRF for development
    JWT_ACCESS_COOKIE_NAME = 'authToken'  # Must match cookie name in auth.js!
    JWT_REFRESH_COOKIE_NAME = 'refreshToken'
    JWT_COOKIE_SAMESITE = 'Strict'
    
    # User Roles
    USER_ROLES = {
        'ADMIN': 'admin',
        'ADOPTER': 'adopter',
        'SHELTER_STAFF': 'shelter_staff'
    }
    
    # OAuth Settings (for future Google login)
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # EMAIL SETTINGS
    EMAIL_USER = os.environ.get('EMAIL_USER') or "ifrashaikh701@gmail.com"
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD') or "lskk hhmw kmjg pjrj"
    
    # TWILIO SETTINGS
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID') or "ACea010f12673fb4f61dffc2a37aa8fa2c"
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN') or "9e5117ba8a14079a94f0bfcb30c9e799"
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER') or "+918483803769"