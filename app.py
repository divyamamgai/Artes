import random
import string

from flask import (Flask,
                   session as flask_session,
                   render_template)
from flask_sqlalchemy import SQLAlchemy
from config import BaseConfig

app = Flask(__name__)
app.config.from_object(BaseConfig)
db = SQLAlchemy(app)

from models import *


def generate_token():
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits) for i in
        range(32))


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET'])
def login():
    login_state = generate_token()
    flask_session['login_state'] = login_state
    return render_template('login.html', login_state=login_state)


if __name__ == '__main__':
    app.run()
