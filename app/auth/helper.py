from flask import request, make_response, jsonify
from app.models import User
from functools import wraps


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[0]
            except IndexError:
                return make_response(jsonify({
                    'status' : 'failed',
                    'message' : 'Provide a valid auth token'
                })), 403

        if not token:
            return make_response(jsonify({
                'status' : 'failed',
                'message' : 'Token is missing'
            })), 401

        try:
            decode_response = User.decode_auth_token(token)
            current_user = User.query.filter_by(id=decode_response).first()
        except:
            message = 'Invalid token'
            if isinstance(decode_response, str):
                message = decode_response
            return make_response(jsonify({
                'status' : 'failed',
                'message' : message
            })), 401

        return f(current_user, *args, **kwargs)
        
    return decorated_function


def response(status, message, status_code):
    return make_response(jsonify({
        'status' : status, 
        'message' : message
    })), status_code

def response_token (status, message, token, status_code):
    return make_response(jsonify({
        'status' : status,
        'message' : message,
        'auth_token' : token.decode('utf-8')
        })), status_code

def response_auth(status, message, token, status_code, user_id, user_email):
    return make_response(jsonify({
        'status' : status,
        'message' : message,
        'id' : user_id,
        'email' : user_email,
        'auth_token' : token.decode('utf-8')
    })), status_code