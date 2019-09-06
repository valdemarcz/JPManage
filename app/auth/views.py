from app import bcrypt
from flask import Blueprint, request
from flask.views import MethodView
from app.models import User, BlackListToken
from app.auth.helper import response, response_auth, token_required, response_token
from sqlalchemy import exc
import re
from .. import db

auth = Blueprint('auth', __name__)


class RegisterUser(MethodView):
    def post(self):
        if request.content_type == 'application/json':
            post_data = request.get_json()
            email = post_data.get('email')
            name = post_data.get('name')
            username = post_data.get('username')
            password = post_data.get('password')
            if re.match(r"[^@]+@[^@]+\.[^@]+", email) and len(password) > 4:
                user = User.query.filter_by(email=email).first()
                if not user:
                    try:
                        user = User(email=email, password=password, username=username, name=name)
                        db.session.add(user)
                        db.session.commit()
                        token = user.encode_auth_token(user.id)
                        return response_token('success', 'Successfully registered', token, 201)
                    except Exception as e:
                       return response('failed', 'Error occured, try again', 401) 
                else:
                    return response('failed', 'Failed, User already exists, Plese sign in', 400)
            return response('failed', 'Missing or wrong email format or password is less than four chars', 400)
        return response('failed', 'Content-type must be json', 400)


class LoginUser(MethodView):
    def post(self):
        if request.content_type == 'application/json':
            post_data = request.get_json()
            email = post_data.get('email')
            password = post_data.get('password')
            if re.match(r"[^@]+@[^@]+\.[^@]+", email) and len(password) > 4:
                user = User.get_by_email(email)
                if user and bcrypt.check_password_hash(user.password, password):
                    return response_auth('success', 'Successfully logged in', user.encode_auth_token(user.id), 200, user.id, email)
                return response('failed', 'User does not exist or password is incorrect', 401)
            return response('failed', 'Missing or wrong email format or password is less than four chars', 401)
        return response('failed', 'Content-type must be json', 202)


class LogOutUser(MethodView):
    """
    Class to log out a user
    """

    def post(self):
        """
        Try to logout a user using a token
        :return:
        """
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                auth_token = auth_header.split(" ")[0]
            except IndexError:
                return response('failed', 'Provide a valid auth token', 403)
            else:
                decoded_token_response = User.decode_auth_token(auth_token)
                if not isinstance(decoded_token_response, str):
                    token = BlackListToken(auth_token)
                    token.blacklist()
                    return response('success', 'Successfully logged out', 200)
                return response('failed', decoded_token_response, 401)
        return response('failed', 'Provide an authorization header', 403)



@auth.route('/auth/reset/passord', methods=['POST'])
@token_required
def reset_password(current_password):
    if request.content_type == 'application/json':
        data = request.get_json()
        old_password = data.get('oldPassword')
        new_password = data.get('newPassword')
        password_confirmation = data.get('passwordConfirmation')
        if not old_password or not new_password or not password_confirmation:
            return response('failed', 'Missing required attributes', 400)
        if bcrypt.check_password_hash(current_user.passord, old_password.encode('utf-8')):
            if not new_password == password_confirmation:
                return response('failed', 'New passwords do not match', 400)
            if not len(new_password) > 4:
                return response('failed', 'New password should be greater than four chars long', 400)
            current_user.reset_password(new_password)
            return response('success', 'Password reset successfully', 200)
        return response('failed', 'Incorrect password', 401)
    return response('failed', 'Content-type must be json', 400)


registration_view = RegisterUser.as_view('register')
login_view = LoginUser.as_view('login')
logout_view = LogOutUser.as_view('logout')

auth.add_url_rule('/auth/register', view_func=registration_view, methods=['POST'])
auth.add_url_rule('/auth/login', view_func=login_view, methods=['POST'])
auth.add_url_rule('/auth/logout', view_func=logout_view, methods=['POST'])