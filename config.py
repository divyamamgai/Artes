import json
import os


class BaseConfig(object):
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super_secret_key')
    DEBUG = os.environ.get('DEBUG', True)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                             'postgres://postgres:postgres'
                                             '@localhost:5432/postgres')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_CLIENT_ID = json.loads(open('google_client_secret.json',
                                       'r').read()).get('web').get('client_id')
