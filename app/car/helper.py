from flask import make_response, jsonify, url_for
from app import app
from app.models import User

def response_for_user_car(user_car):
    return make_response(jsonify({
        'ststus' : 'success',
        'car' : user_car
    })), 200

def response_for_get_cars(cars):
    return make_response(jsonify({
        'status' : 'success',
        'cars' : cars
    }))

def response_for_added_car(user_car, status_code):
    return make_response(jsonify({
        'status' : 'success',
        'id' : user_car.id,
        'make' : user_car.make,
        'model' : user_car.model,
        'createdAt' : user_car.created_at,
        'modifiedAt' : user_car.modified_at
    })), status_code

def response(status, message, code):
    return make_response(jsonify({
        'status' : status,
        'message' : message
    })), code

def get_user_car_json_list(user_cars):
    cars = []
    for user_car in user_cars:
        cars.append(user_car.json())
    return cars

