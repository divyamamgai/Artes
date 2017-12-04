import os


class BaseConfig(object):
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super_secret_key')
    DEBUG = os.environ.get('DEBUG', True)
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
