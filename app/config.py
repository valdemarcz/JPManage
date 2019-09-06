import os

base_dir = os.path.abspath(os.path.dirname(__file__))


secret = os.urandom(24)

class BaseConfig:
    DEBUG = True
    SECRET_KEY = os.getenv('SECRET_KEY', secret)
    BCRYPT_HASH_PREFIX = 14
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTH_TOKEN_EXPIRY_DAYS = 30
    AUTH_TOKEN_EXPIRY_SECONDS = 3000
    BUCKET_AND_ITEMS_PER_PAGE = 25


class DevelopmentConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    BCRYPT_HASH_PREFIX = 4
    AUTH_TOKEN_EXPIRY_DAYS = 1
    AUTH_TOKEN_EXPIRY_SECONDS = 20
    BUCKET_AND_ITEMS_PER_PAGE = 4


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    BCRYPT_HASH_PREFIX = 13
    AUTH_TOKEN_EXPIRY_DAYS = 30
    AUTH_TOKEN_EXPIRY_SECONDS = 20
    BUCKET_AND_ITEMS_PER_PAGE = 10