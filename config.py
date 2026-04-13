# App configuration
import os

class Config:
    APP_DEBUG = os.getenv('APP_DEBUG') or True
    APP_ENV = os.getenv('APP_ENV') or 'development'
    SECRET_KEY = os.getenv('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'notes.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False