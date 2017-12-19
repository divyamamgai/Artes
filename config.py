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
    # Number of top endorsement for which to show detailed information such
    # as endorsers images as profile links.
    ENDORSEMENT_TOP_LIMIT = 5
    # Number of endorsers to show for each each top endorsement for the user.
    ENDORSER_DETAIL_LIMIT = 5
