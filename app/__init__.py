#app/__init__.py
#docks not imported!!!
import os
from flask import Flask
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager, current_user
from flask_sslify import SSLify
from flask_wtf.csrf import CSRFProtect, CSRFError

app = Flask(__name__, static_folder="web/static", template_folder="web/templates")
sslify = SSLify(app)
app.config['UPLOADED_PHOTOS_DEST'] = os.getcwd() + '/app/web/static'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
DEBUG = True
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['BCRYPT_HASH_PREFIX'] = 14
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['AUTH_TOKEN_EXPIRY_DAYS'] = 30
app.config['AUTH_TOKEN_EXPIRY_SECONDS'] = 3000
app.config['BUCKET_AND_ITEMS_PER_PAGE'] = 25

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)

csrf = CSRFProtect(app)
CORS(app)

app_settings = os.getenv(
    'APP_SETTINGS',
    'app.config.DevelopmentConfig'
)

app.config.from_object(app_settings)

bcrypt = Bcrypt(app)

db = SQLAlchemy(app)


from .models import User, Car

from app import views

from app.auth.views import auth

app.register_blueprint(auth, url_prefix='/api/v1')

from app.car.views import carapi

app.register_blueprint(carapi, url_prefix='/api/v1')

from app.web.views import web

app.register_blueprint(web)

from app.web.main import authweb

app.register_blueprint(authweb)

from app.web.main import mainweb

app.register_blueprint(mainweb)

