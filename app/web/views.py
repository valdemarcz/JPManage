from flask import Blueprint, request, abort, g, render_template
from app.auth.helper import token_required
from app.car.helper import response, response_for_added_car, response_for_user_car, get_user_car_json_list, response_for_get_cars
from app.models import User, Car, CarSchema
import datetime

web = Blueprint('web', __name__)

@web.route('/home')
def index():
    return render_template('home.html')


@web.route('/about')
def about():
    return render_template('about.html')