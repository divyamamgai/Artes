import os


class BaseConfig(object):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = os.environ.get('DEBUG')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
