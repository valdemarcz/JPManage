from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from ..models import User
from .. import db
import datetime

authweb = Blueprint('authweb', __name__)

@authweb.route('/login')
def login():
    return render_template('login.html')

@authweb.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    if not user and not check_password_hash(user.password, password):
        flash('Please check your login detail and try again.')
        return redirect(url_for('authweb.login'))

    login_user(user)

    return redirect(url_for('mainweb.index'))

@authweb.route('/signup')
def signup():
    return render_template('signup.html')


@authweb.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    registered_on = datetime.datetime.utcnow()

    user = User.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists. ')
        return redirect(url_for('authweb.signup'))

    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'), registered_on=registered_on)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('authweb.login'))

@authweb.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('mainweb.index'))