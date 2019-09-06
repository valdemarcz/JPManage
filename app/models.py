from flask_login import UserMixin
from app import app, db, bcrypt
import datetime
import jwt
from marshmallow import fields, Schema
from flask_login import current_user
from flask import flash
from werkzeug.security import generate_password_hash, check_password_hash
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    image_file = db.Column(db.String(30), nullable=False, default='default_prof_pic.jpg')
    password = db.Column(db.String(255), nullable=False)
    admin = db.Column(db.Boolean,nullable=True, default=False)
    name = db.Column(db.String(1000))
    registered_on = db.Column(db.DateTime, nullable=False)
    date_reserved = db.relationship('ReservedDate')
    #roles = db.relationship('Role', secondary='roles_users',
    #                    backref=db.backref('users', lazy='dynamic'))


    
    def __init__(self, email, admin=False):
        self.email = email
        self.admin = admin
        self.registered_on = datetime.datetime.now()
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.id

    def is_admin(self):
        if self.admin == True:
            return True

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self.encode_auth_token(self.id)


    def encode_auth_token(self, user_id):
        try:
            payload = {
                'exp' : datetime.datetime.utcnow() + datetime.timedelta(days=app.config.get('AUTH_TOKEN_EXPIRY_DAYS'),seconds=app.config.get('AUTH_TOKEN_EXPIRY_SECONDS')),
                'iat' : datetime.datetime.utcnow(),
                'sub' : user_id
            }
            return jwt.encode(
                payload,
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(token):
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
            is_token_blacklisted = BlackListToken.check_blacklist(token)
            if is_token_blacklisted:
                return 'Token was Blacklisted, Please login'
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired, please sign in again'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please sign in again'


    @staticmethod
    def get_by_id(user_id):
        return User.query.filter_by(id=user_id).first() 

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()

    def reset_password(self, new_password):
        self.password = bcrypt.generate_password_hash(new_password, app.config.get('BCRYPT_LOG_ROUNDS')) \
            .decode('utf-8')
        db.session.commit()


class BlackListToken(db.Model):
    __tablename__ = 'blacklist_token'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.datetime.now()

    def blacklist(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def check_blacklist(token):
        response = BlackListToken.query.filter_by(token=token).first()
        if response:
            return True
        return False

option_car_rel = db.Table('option_for_car', 
    db.Column('car_id', db.Integer, db.ForeignKey('cars.id')),
    db.Column('option_id', db.Integer, db.ForeignKey('options.id')),
    db.PrimaryKeyConstraint('car_id', 'option_id')
    )

photo_car_rel = db.Table('photo_for_car', 
    db.Column('car_id', db.Integer, db.ForeignKey('cars.id')),
    db.Column('photo_id', db.Integer, db.ForeignKey('photos.id')),
    db.PrimaryKeyConstraint('car_id', 'photo_id')
    )

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    subj = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=True)
    isconfirmed = db.Column(db.Boolean,nullable=True, default=False)
    answer = db.Column(db.Text, nullable=True)
    


class Car(db.Model):
    __tablename__ = 'cars'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    make = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    prod_year = db.Column(db.Integer, nullable=True)
    pyear = db.Column(db.Integer, nullable=True)
    prod_month = db.Column(db.Integer, nullable=True)
    mileage = db.Column(db.Integer, nullable=True)
    engine_capacity = db.Column(db.String(20), nullable=True)
    engine_power = db.Column(db.Integer, nullable=True)
    fuel_type = db.Column(db.String(20), nullable=True)
    gearbox = db.Column(db.String(20), nullable=True)
    steering_wheel_side = db.Column(db.String(20), nullable=True)
    body_type = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)
    number_of_doors = db.Column(db.Integer, nullable=True)
    color = db.Column(db.String(30), nullable=True)
    driven_wheels = db.Column(db.String(30), nullable=True)
    VIN = db.Column(db.String(100), nullable=True)
    wheel_size = db.Column(db.Integer, nullable=True)
    MOT_test = db.Column(db.Date, nullable=True)
    damage = db.Column(db.String(40), nullable=True)
    price = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=True, default="Proposed")
    owner_id = db.Column(db.Integer,nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    modified_at = db.Column(db.DateTime, nullable=False)
    options = db.relationship('Options', secondary=option_car_rel, backref=db.backref('options_of_car', lazy='dynamic'))
    photos = db.relationship('Photos', secondary=photo_car_rel, backref=db.backref('photos_of_car', lazy='dynamic'))
    date_reserved = db.relationship('ReservedDate')


    def __init__(self):
        owner_id = current_user.get_id()
        created_at = datetime.datetime.utcnow()
        modified_at = datetime.datetime.utcnow()
  
    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self, data):
        for key, item in data.items():
            setattr(self, key, item)
            self.modified_at = datetime.datetime.utcnow()
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.update()

    @staticmethod
    def get_all_cars():
        return Car.query.all()

    @staticmethod
    def get_car_by_id(car_id):
        return Car.query.get(car_id)

    def json(self):
        return{
            'id' : self.id,
            'make' : self.make,
            'model' : self.model,
            'prod_year' : self.prod_year.isoformat(),
            'mileage' : self.mileage,
            'engine_capacity' : self.engine_capacity,
            'engine_power' : self.engine_power,
            'fuel_type' : self.fuel_type,
            'gearbox' : self.gearbox,
            'steering_wheel_side' : self.steering_wheel_side,
            'body_type' : self.body_type,
            'description' : self.description,
            'number_of_doors' : self.number_of_doors,
            'color' : self.color,
            'driven_wheels' : self.driven_wheels,
            'VIN' : self.VIN,
            'wheel_size' : self.wheel_size,
            'MOT_test' : self.MOT_test.isoformat(),
            'damage' : self.damage,
            'price' : self.price,
            'createdAt' : self.created_at.isoformat(),
            'modifiedAt' : self.modified_at.isoformat()
        }



   



class Makes(db.Model):
    __tablename__ = 'makes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    make = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return '%r' %self.make


class RequestDelete(db.Model):
    __tablename__ = 'requests_delete'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '%r' %self.reason

class Models(db.Model):
    __tablename__ = 'models'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    make = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return '%r' %self.model

class Body(db.Model):
    __tablename__ = 'body'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    body = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return '%r' %self.body

class Fuel(db.Model):
    __tablename__ = 'fuel'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fuel = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return '%r' %self.fuel

class Gearbox(db.Model):
    __tablename__ = 'gearbox'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gearbox = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return '%r' %self.gearbox

class NumDoors(db.Model):
    __tablename__ = 'doors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    doors = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return '%r' %self.doors

class WheelSide(db.Model):
    __tablename__ = 'wheel'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wheel = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return '%r' %self.wheel

class Color(db.Model):
    __tablename__ = 'color'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    color = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return '%r' %self.color

class Options(db.Model):
    __tablename__ = 'options'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    option = db.Column(db.String(100), nullable=True)


    def __repr__(self):
        return '%r' %self.option

class Photos(db.Model):
    __tablename__ = 'photos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    photo_name = db.Column(db.String(300), nullable=False)


    def __repr__(self):
        return self.photo_name

class Dates(db.Model):
    __tablename__ = 'dates'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    hour_from = db.Column(db.Integer, nullable=False)
    hour_to = db.Column(db.Integer, nullable=False)
    
    

class ReservedDate(db.Model):
    __tablename__ = 'reserved'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    hour = db.Column(db.Integer, nullable=False)

class CarSchema(Schema):
    id = fields.Int(dump_only=True)
    make = fields.Str(required=True)
    model = fields.Str(required=True)
    price = fields.Int(required=True)
    prod_year = fields.Integer(required=False)
    prod_month = fields.Integer(required=False)
    mileage = fields.Int(required=False)
    engine_capacity = fields.Str(required=False)
    engine_power = fields.Int(required=False)
    fuel_type = fields.Str(required=False)
    gearbox = fields.Str(required=False)
    steering_wheel_side = fields.Str(required=False)
    body_type = fields.Str(required=False)
    description = fields.Str(required=False)
    number_of_doors = fields.Int(required=False)
    color = fields.Str(required=False)
    driven_wheels = fields.Str(required=False)
    VIN = fields.Str(required=False)
    wheel_size = fields.Int(required=False)
    MOT_test = fields.Date(required=False)
    damage = fields.Str(required=False)
    owner_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    modified_at = fields.DateTime(dump_only=True)

