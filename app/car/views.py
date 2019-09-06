from flask import Blueprint, request, abort, g
from app.auth.helper import token_required
from app.car.helper import response, response_for_added_car, response_for_user_car, get_user_car_json_list, response_for_get_cars
from app.models import User, Car, CarSchema
import datetime

carapi = Blueprint('carapi', __name__)

car_schema = CarSchema()
cars_schema = CarSchema(many=True)


@carapi.route('/mycars/', methods=['GET'])
@token_required
def mycarslist(current_user):
    user = User.get_by_id(current_user.id)
    cars = Car.query.filter_by(owner_id=user.id).all()
    data = cars_schema.dump(cars, many=True).data
    return response_for_get_cars(data)


@carapi.route('/cars/', methods=['GET'])
def allcarslist():
    allcars = Car.get_all_cars()
    data = cars_schema.dump(allcars, many=True).data
    return response_for_get_cars(data)


@carapi.route('/cars/<int:car_id>/', methods=['GET'])
@token_required
def get_car_by_id(current_user, car_id):
    car = Car.get_car_by_id(car_id)
    if not car:
        return response('failed', 'car not found', 404)
    data = car_schema.dump(car).data
    return response_for_user_car(data)


@carapi.route('/cars/', methods=['POST'])
@token_required
def add_car(current_user):
    json_data = request.get_json()
    json_data['owner_id'] = current_user.id
    json_data['created_at'] = datetime.datetime.utcnow()
    data, error = car_schema.load(json_data)
    if error:
        return response('failed', error, 400)

    car = Car(current_user.id, data)
    car.save()
    data = car_schema.dump(car).data
    return response_for_added_car(car, 201)    


@carapi.route('/cars/<int:car_id>/', methods=['PUT'])
@token_required
def update_car(current_user, car_id):
    if request.content_type == 'application/json' :
        req_data = request.get_json()
        car = Car.get_car_by_id(car_id)
        if not car:
            return response('failed', 'car not found', 404)
        data = cars_schema.dump(car).data
        if data.get('owner_id') != current_user.id:
            return response('failed', 'It\'s not your car', 400)
        data, error = cars_schema.load(req_data, partial=True)
        if error:
            return response('failed', error, 400)
        car.update(data)
        data = cars_schema.dump(car).data
        return response_for_get_cars(data)


@carapi.route('/cars/<int:car_id>/', methods=['DELETE'])
@token_required
def delete_car(current_user, car_id):
    car = Car.get_car_by_id(car_id)
    if not car:
        return response('failed', 'car not found', 404)
    data = cars_schema.dump(car).data
    if data.get('owner_id') != current_user.id:
            return response('failed', 'It\'s not your car', 400)
    car.delete()

    return response('success', 'car deleted', 204)