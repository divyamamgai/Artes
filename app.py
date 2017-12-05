import json
import random
import ssl
import string

import httplib2
from flask import (flash,
                   Flask,
                   make_response,
                   session as flask_session,
                   url_for,
                   redirect,
                   render_template,
                   request)
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc as sqlalchemy_exc
from config import BaseConfig

app = Flask(__name__)
app.config.from_object(BaseConfig)
db = SQLAlchemy(app)

from models import *


def generate_token():
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits) for i in
        range(32))


def get_user_id(email):
    """Get User ID using User Email"""
    user = db.session.query(User).filter_by(email=email).first()
    if user:
        return user.id
    else:
        return None


def create_user(name, email, image_url, google_plus_link):
    """Create a new User using the details provided"""
    try:
        user = User(name=name, email=email, image_url=image_url,
                    google_plus_link=google_plus_link)
        db.session.add(user)
        db.session.commit()
        return user
    except sqlalchemy_exc.IntegrityError:
        return None


@app.route('/login', methods=['GET'])
def login():
    login_state = generate_token()
    flask_session['login_state'] = login_state
    return render_template('login.html', login_state=login_state)


@app.route('/login/google/<string:login_state>', methods=['POST'])
def login_google(login_state):
    if login_state != flask_session.get('login_state'):
        response = make_response(json.dumps('Invalid login state parameter.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    auth_code = request.data

    try:
        # Exchange auth code received for access token using the Google App
        # Client secrets.
        oauth_flow = flow_from_clientsecrets('google_client_secret.json',
                                             scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(auth_code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    h = httplib2.Http()
    try:
        # Request token info to make sure it is in valid state.
        token_info_result = json.loads(
            h.request(
                'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token'
                '=%s' % access_token,
                'GET')[1].decode('utf-8'))
    except ssl.SSLEOFError:
        response = make_response(json.dumps(
            'Error occurred while requesting token info from Google Plus.'),
            500)
        response.headers['Content-Type'] = 'application/json'
        return response

    if token_info_result.get('error') is not None:
        response = make_response(json.dumps(token_info_result.get('error')),
                                 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    google_plus_id = credentials.id_token['sub']

    if token_info_result.get('user_id') != google_plus_id:
        response = make_response(
            json.dumps('Token\'s user ID does not match given user ID.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if token_info_result.get('issued_to') != app.config.get(
            'GOOGLE_CLIENT_ID'):
        response = make_response(
            json.dumps('Token\'s client ID does not match app\'s.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = flask_session.get('access_token')
    stored_google_plus_id = flask_session.get('google_plus_id')
    if stored_access_token is not None \
            and google_plus_id == stored_google_plus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        # Request user info using the access token.
        user_info_result = json.loads(
            h.request(
                'https://www.googleapis.com/oauth2/v1/userinfo?access_token'
                '=%s&alt=json' % access_token,
                'GET')[1].decode('utf-8'))
    except ssl.SSLEOFError:
        response = make_response(json.dumps(
            'Error occurred while requesting user info from Google Plus.'),
            500)
        response.headers['Content-Type'] = 'application/json'
        return response

    flask_session['provider'] = 'google'
    flask_session['access_token'] = access_token
    flask_session['google_plus_id'] = google_plus_id
    flask_session['name'] = user_info_result.get('name')
    flask_session['email'] = user_info_result.get('email')
    flask_session['image_url'] = user_info_result.get('picture')
    flask_session['google_plus_link'] = user_info_result.get('link')

    # user_id = get_user_id(flask_session.get('email'))
    # # If user does not exists create a new user.
    # if not user_id:
    #     user_id = create_user(flask_session.get('name'),
    #                           flask_session.get('email'),
    #                           flask_session.get('image_url'),
    #                           flask_session.get('google_plus_link')).id
    #     if not user_id:
    #         # If user creation failed delete already assigned session keys.
    #         del flask_session['access_token']
    #         del flask_session['google_plus_id']
    #         del flask_session['name']
    #         del flask_session['email']
    #         del flask_session['image_url']
    #         del flask_session['google_plus_link']
    #         response = make_response(
    #             json.dumps('Error occurred while creating user.'), 500)
    #         response.headers['Content-Type'] = 'application/json'
    #         return response
    #
    # flask_session['user_id'] = user_id

    response = make_response(json.dumps(
        'User "%s" logged in successfully.' % flask_session.get('name')), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/logout')
def logout():
    if 'access_token' in flask_session:
        logout_response = logout_google()
        if logout_response.status_code != 200:
            flash('Error occurred while trying to logout via Google Plus.')
            return redirect(url_for('index'))

        # On successful logout delete session keys.
        del flask_session['name']
        del flask_session['email']
        # del flask_session['user_id']
        del flask_session['provider']
        del flask_session['login_state']

        flash('You have been successfully logged out!')
        return redirect(url_for('index'))
    else:
        flash('You were not logged in!')
        return redirect(url_for('index'))


@app.route('/logout/google')
def logout_google():
    access_token = flask_session.get('access_token')
    if not access_token:
        response = make_response(
            json.dumps('User is not connected via Google Plus.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    h = httplib2.Http()
    try:
        revoke_token_result = h.request(
            'https://accounts.google.com/o/oauth2/revoke?token=%s'
            % access_token,
            'GET')[0]
    except ssl.SSLEOFError:
        response = make_response(json.dumps(
            'Error occurred while requesting to revoke Google Plus token.',
            500))
        response.headers['Content-Type'] = 'application/json'
        return response

    if revoke_token_result['status'] == '200':
        del flask_session['access_token']
        del flask_session['google_plus_id']

        response = make_response(
            json.dumps('Successfully disconnected from Google Plus.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke Google Plus token.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/', methods=['GET'])
def index():
    if 'access_token' not in flask_session:
        flash('You need to login to access your profile!')
        return redirect(url_for('login'))
    return render_template('index.html', flask_session=flask_session)


if __name__ == '__main__':
    app.run()
