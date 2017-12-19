import json
import random
import ssl
import string
from functools import wraps

import httplib2
from flask import (flash,
                   Flask,
                   make_response,
                   session as flask_session,
                   url_for,
                   redirect,
                   render_template,
                   request)
from flask_sqlalchemy import SQLAlchemy
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from sqlalchemy import exc as sqlalchemy_exc
from sqlalchemy import sql as sqlalchemy_sql
from sqlalchemy import func as sqlalchemy_func
from sqlalchemy import text as sqlalchemy_text

from config import BaseConfig

app = Flask(__name__)
app.config.from_object(BaseConfig)
db = SQLAlchemy(app)

from models import *


def generate_token():
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits) for i in
        range(32))


def get_user(email):
    user = db.session.query(User).filter_by(email=email).first()

    return user


def create_user(name, email, image_url, google_plus_link):
    user = User(name=name, email=email, image_url=image_url,
                google_plus_link=google_plus_link)
    db.session.add(user)
    db.session.commit()
    return user


def get_skill(skill_id):
    skill = db.session.query(Skill).filter_by(id=skill_id).first()

    return skill


def get_user_skills(user_id):
    skills = db.session.query(Skill) \
        .join(UserSkill, UserSkill.skill_id == Skill.id) \
        .filter(UserSkill.user_id == user_id) \
        .all()

    return skills


def get_user_skill(user_id, skill_id):
    user_skill = db.session.query(UserSkill) \
        .filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id) \
        .first()

    return user_skill


def get_endorse_counts(user_id):
    endorse_counts = db.session.query(UserSkill.user_id, UserSkill.skill_id,
                                      sqlalchemy_func.count(
                                          Endorse.endorser_id).label(
                                          'endorse_count')) \
        .filter(UserSkill.user_id == user_id) \
        .outerjoin(Endorse,
                   sqlalchemy_sql.and_(
                       Endorse.user_id == UserSkill.user_id,
                       Endorse.skill_id == UserSkill.skill_id)) \
        .group_by(UserSkill.user_id, UserSkill.skill_id) \
        .order_by(sqlalchemy_text('endorse_count DESC')) \
        .all()

    return endorse_counts


def get_self_endorses(user_id, endorser_id):
    self_endorses = db.session.query(Endorse.skill_id,
                                     sqlalchemy_sql.literal(True)) \
        .filter(Endorse.user_id == user_id,
                Endorse.endorser_id == endorser_id) \
        .all()

    return dict(self_endorses)


def get_endorse(user_id, skill_id, endorser_id):
    endorse = db.session.query(Endorse) \
        .filter(Endorse.user_id == user_id,
                Endorse.skill_id == skill_id,
                Endorse.endorser_id == endorser_id) \
        .first()

    return endorse


def get_endorsers(user_id, skill_id):
    endorsers = db.session.query(Endorse.user_id, User) \
        .join(User, User.id == Endorse.endorser_id) \
        .filter(Endorse.user_id == user_id, Endorse.skill_id == skill_id) \
        .limit(app.config.get('ENDORSER_DETAIL_LIMIT')) \
        .all()

    return map(lambda endorser: endorser[1], endorsers)


@app.route('/login', methods=['GET'])
def login():
    login_state = generate_token()
    flask_session['login_state'] = login_state

    return render_template('login.html', login_state=login_state)


@app.route('/login/google/<string:login_state>', methods=['POST'])
def login_google(login_state):
    if login_state != flask_session.get('login_state'):
        response = make_response(json.dumps('Invalid login state parameter!'),
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
            json.dumps('Failed to upgrade the authorization code!'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    h = httplib2.Http()
    try:
        # Request token info to make sure it is in valid state.
        token_info_result = json.loads(
            h.request(
                'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token'
                '=%s' % access_token, 'GET')[1].decode('utf-8'))
    except ssl.SSLEOFError:
        response = make_response(json.dumps(
            'Error occurred while requesting token info from Google Plus!'),
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
            json.dumps('Token\'s user ID does not match given user ID!'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if token_info_result.get('issued_to') != app.config.get(
            'GOOGLE_CLIENT_ID'):
        response = make_response(
            json.dumps('Token\'s client ID does not match that of app!'), 401)
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

    user = get_user(user_info_result.get('email'))

    # If user does not exists create a new user.
    if not user:
        try:
            user = create_user(user_info_result.get('name'),
                               user_info_result.get('email'),
                               user_info_result.get('picture'),
                               user_info_result.get('link'))

        except sqlalchemy_exc.SQLAlchemyError:
            # If user creation failed delete already assigned session keys.
            del flask_session['provider']
            del flask_session['access_token']
            del flask_session['google_plus_id']

            response = make_response(
                json.dumps('Error occurred while creating user!'), 500)
            response.headers['Content-Type'] = 'application/json'
            return response

    flask_session['user'] = user.serialize

    response = make_response(json.dumps(
        'User "%s" logged in successfully.' % flask_session.get('name')), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/logout')
def logout():
    if 'access_token' in flask_session:
        logout_response = logout_google()
        if logout_response.status_code != 200:
            flash('Error occurred while trying to logout from Google Plus!')
            return redirect(url_for('index'))

        # On successful logout delete session keys.
        del flask_session['provider']
        del flask_session['user']

        flash('You have been successfully logged out!')
        return redirect(url_for('login'))
    else:
        flash('You were not logged in!')
        return redirect(url_for('index'))


@app.route('/logout/google')
def logout_google():
    access_token = flask_session.get('access_token')
    if not access_token:
        response = make_response(
            json.dumps('User is not connected from Google Plus!'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    h = httplib2.Http()
    try:
        revoke_token_result = h.request(
            'https://accounts.google.com/o/oauth2/revoke?token=%s'
            % access_token, 'GET')[0]

    except ssl.SSLEOFError:
        response = make_response(json.dumps(
            'Error occurred while requesting to revoke Google Plus token!'),
            500)
        response.headers['Content-Type'] = 'application/json'
        return response

    if revoke_token_result['status'] == '200':
        del flask_session['access_token']
        del flask_session['google_plus_id']

        response = make_response(
            json.dumps('Successfully disconnected from Google Plus!'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke Google Plus token.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


def authorized(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if 'access_token' not in flask_session:
            response = make_response(
                'You need to be logged in to access this resource!', 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        return func(*args, **kwargs)

    return decorated


def authorized_redirect(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if 'access_token' not in flask_session:
            flash('You need to be logged in to access this page!')
            return redirect(url_for('login'))
        return func(*args, **kwargs)

    return decorated


@app.route('/', methods=['GET'])
@authorized_redirect
def index():
    return redirect(
        url_for('user_profile', email=flask_session.get('user').get('email')))


@app.route('/skills/search/<string:name>', methods=['GET'])
@authorized_redirect
def skills_search(name):
    user_id = flask_session.get('user').get('id')

    skills = db.session.query(Skill) \
        .filter(Skill.name.like('%' + name + '%')) \
        .filter(~sqlalchemy_sql.exists(['skill_id'])
                .where(sqlalchemy_sql
                       .and_(UserSkill.user_id == user_id,
                             UserSkill.skill_id == Skill.id)))

    response = make_response(
        json.dumps(map((lambda x: x.serialize), skills.all())),
        200)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/skills/add/', methods=['POST'])
@authorized
def skills_add():
    skill_ids = request.form.getlist('skill_ids[]')

    if len(skill_ids) > 0:
        user_id = flask_session.get('user').get('id')
        added_skills = []

        try:
            for skill_id in skill_ids:
                skill = get_skill(skill_id)

                if skill is not None:
                    user_skill = UserSkill(user_id=user_id, skill_id=skill_id)
                    db.session.add(user_skill)
                    added_skills.append(skill)

            db.session.commit()

            response = make_response(
                json.dumps(map((lambda x: x.serialize), added_skills)), 201)

        except sqlalchemy_exc.SQLAlchemyError:
            response = make_response(
                json.dumps('Error occurred while adding skills!'), 500)

    else:
        response = make_response(json.dumps('No skills were provided!'), 400)

    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/user/<int:user_id>/endorse/<int:skill_id>',
           methods=['POST', 'DELETE'])
@authorized
def user_skill_endorse(user_id, skill_id):
    user_skill = get_user_skill(user_id, skill_id)
    endorser_id = flask_session.get('user').get('id')

    if user_skill is not None:
        if request.method == 'POST':
            try:
                endorse = Endorse(user_id=user_id, skill_id=skill_id,
                                  endorser_id=endorser_id)
                db.session.add(endorse)
                db.session.commit()

                response = make_response(json.dumps(endorse.serialize), 200)
            except sqlalchemy_exc.SQLAlchemyError:
                response = make_response(
                    json.dumps('Error occurred while creating endorsement!'),
                    400)

        elif request.method == 'DELETE':
            try:
                endorse = get_endorse(user_id, skill_id, endorser_id)
                db.session.delete(endorse)
                db.session.commit()

                response = make_response(json.dumps(endorse.serialize), 200)
            except sqlalchemy_exc.SQLAlchemyError:
                response = make_response(
                    json.dumps('Error occurred while deleting endorsement!'),
                    400)

        else:
            response = make_response(json.dumps('Invalid request method!'),
                                     400)
    else:
        response = make_response(json.dumps('User skill does not exists!'),
                                 400)

    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/user/<string:email>', methods=['GET'])
@authorized_redirect
def user_profile(email):
    user = get_user(email).serialize

    skills = get_user_skills(user.get('id'))

    skills_dict = dict(map(lambda skill: (skill.id, skill.name), skills))

    endorse_counts = get_endorse_counts(user.get('id'))

    top_skills = map(lambda endorse_count: endorse_count[1],
                     filter(lambda endorse_count: endorse_count[2] > 0,
                            endorse_counts[
                            :app.config.get('ENDORSEMENT_TOP_LIMIT')]))

    endorsers = dict(map(lambda top_skill: (
        top_skill, get_endorsers(user.get('id'), top_skill)), top_skills))

    self_endorses = get_self_endorses(user.get('id'),
                                      flask_session.get('user').get('id'))

    return render_template('user.html', flask_session=flask_session,
                           user=user, skills_dict=skills_dict,
                           endorse_counts=endorse_counts,
                           self_endorses=self_endorses, endorsers=endorsers)


if __name__ == '__main__':
    app.run()
