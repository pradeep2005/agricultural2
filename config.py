import os

class Config:
    # Use os.urandom(24) to generate a strong key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_and_complex_key_for_development'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False