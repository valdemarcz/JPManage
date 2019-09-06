from flask import Blueprint, render_template, url_for, request, redirect, jsonify, flash
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, SelectField, validators, PasswordField
from wtforms.fields.html5 import EmailField
import os, hashlib, time, datetime
from app import photos, db, app
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib import sqla
from ..models import User, Car, Models, RequestDelete, Question, Photos, Makes, Body, Fuel, Gearbox, WheelSide, Options, Color, NumDoors
from app.web.regressor import load_lin_regressor, train_lin_reg, get_plain_data_from_json, write, clear_and_load_data, data_for_prediction_object_preproessing, data_transform, train_regressor, load_regressor, predict
import pandas as pd
from werkzeug import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import datetime
import numpy
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFError

mainweb = Blueprint('mainweb', __name__)


bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.login_view = 'authweb.login'
login_manager.init_app(app)


@app.context_processor
def inject_template_scope():
    injections = dict()

    def cookies_check():
        value = request.cookies.get('cookie_consent')
        return value == 'true'
    injections.update(cookies_check=cookies_check)

    return injections

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()



class MyModelView(sqla.ModelView):
    def is_accessible(self):
        if current_user.is_authenticated:
            user_id = current_user.get_id()
            user = User.query.filter_by(id=user_id).first() 
            return user
        else:
            return False
        
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('authweb.login'))

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if current_user.is_authenticated:
            user_id = current_user.get_id()
            user = User.query.filter_by(id=user_id).first()
            if user.admin == True: 
                return user
            else:
                return False
        return False
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('mainweb.index'))

class UploadForm(FlaskForm):
    photo = FileField(validators=[FileAllowed(photos, u'Image Only!'), FileRequired(u'Choose a file!')])
    make = SelectField('Make', choices=[])
    model = SelectField('Model', choices=[])
    body = SelectField('Body type', choices=[])
    fuel = SelectField('Fuel type', choices=[])
    gearbox = SelectField('Gearbox', choices=[])
    num_doors = SelectField('Number of doors', choices=[])
    steering = SelectField('Steering wheel side', choices=[])
    color = SelectField('Color', choices=[])

    submit = SubmitField(u'Send offer')

class SearchForm(FlaskForm):
    make = SelectField('Make', choices=[])
    model = SelectField('Model', choices=['------'])
    body = SelectField('Body type', choices=[])
    fuel = SelectField('Fuel type', choices=[])
    gearbox = SelectField('Gearbox', choices=[])
    num_doors = SelectField('Number of doors', choices=[])
    color = SelectField('Color', choices=[])
    yearfrom = SelectField('Year from', choices=[])
    yearto = SelectField('Year to', choices=[])
    pricefrom = SelectField('Price from', choices=[])
    priceto = SelectField('Price to', choices=[])
    submit = SubmitField(u'Search')

class ForgotForm(FlaskForm):
    email = EmailField('Email address',
    [validators.DataRequired(), validators.Email()])

class PasswordResetForm(FlaskForm):
    current_password = PasswordField('Current Password',
    [validators.DataRequired(),
    validators.Length(min=4, max=80)])

class RegressorView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        
        if request.method == 'POST':
            f = request.files['file']
            f.save(secure_filename(f.filename))

            train_regressor(f.filename, int(request.form['epochs']), int(request.form['neurons']))

            return self.render('admin/regressor.html')

        return self.render('admin/regressor.html')


class ConfirmRequests(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        requests = RequestDelete.query.all()
        return self.render('admin/requested_delete.html', requests=requests)
    @expose('/delete/<int:user_id>/', methods=['GET', 'POST'])
    def delete(current_user, user_id):
        delete_qusers = User.__table__.delete().where(User.id==user_id)
        
        cars = Car.query.filter_by(owner_id=user_id).all()
        for car in cars:
            car.status = "Deleted user"

        delete_qreqs = RequestDelete.__table__.delete().where(RequestDelete.user_id==user_id)
        
        db.session.execute(delete_qusers)
        db.session.execute(delete_qreqs)
        
        db.session.commit()
        return redirect('/admin/deleting')

class Regressor1View(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        f = open("mae.txt", "r")
        mae_old = f.read() 
        f.close()
        
        if request.method == 'POST':
            f = request.files['file']
            f.save(secure_filename(f.filename))
            mae = train_lin_reg(f.filename)
            f = open("mae.txt", "w")
            f.write(str(mae))
            f.close()
            return self.render('admin/regressor1.html', mae=mae, mae_old=mae_old)
        
        return self.render('admin/regressor1.html', mae_old=mae_old)
class Arrived(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        cars = Car.query.filter_by(status='Confirmed')
        return self.render('admin/arrives.html', cars=cars)
    @expose('/arrived/<int:id_of_car>/', methods=['GET', 'POST'])
    def arrived(self, id_of_car):
        car = Car.query.filter_by(id=id_of_car).first()
        car.status = "Arrived"
        db.session.commit()
        return redirect('/admin/arriving')
    @expose('/delete/<int:id_of_car>/', methods=['GET', 'POST'])
    def delete(current_user, id_of_car):
        car = Car.query.filter_by(id=id_of_car).first()
        car.delete()
        db.session.commit()
        return redirect('/admin/arriving')

class Confirmads(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        cars = Car.query.filter_by(status='Proposed')
        return self.render('admin/confirms.html', cars=cars)
    @expose('/confirm/<int:id_of_car>/', methods=['GET', 'POST'])
    def confirm(self, id_of_car):
        car = Car.query.filter_by(id=id_of_car).first()
        car.status = "Confirmed"
        db.session.commit()
        return redirect('/admin/confirming')
    @expose('/proposition/<int:id_of_car>/', methods=['GET', 'POST'])
    def details(self, id_of_car):
        car = Car.query.filter_by(id=id_of_car).first()
        return self.render('admin/proposition.html', car=car)
    @expose('/change/<int:id_of_car>/', methods=['GET', 'POST'])
    def change(self, id_of_car):
        car = Car.query.filter_by(id=id_of_car).first()
        options = Options.query.all()

        if request.method == 'POST':
            make = request.form.get('make')
            #model = request.form.get('model')
            engine_power = request.form.get('engine_power')
            body = request.form.get('body')
            fuel = request.form.get('fuel')
            engine_capacity = request.form.get('engine_capacity')
            gearbox = request.form.get('gearbox')
            num_doors = request.form.get('num_doors')
            mileage = request.form.get('mileage')
            steering = request.form.get('steering')
            color = request.form.get('color')
            year = str(datetime.datetime.strptime(request.form.get('manufacture'), '%Y-%m').year)
            month = str(datetime.datetime.strptime(request.form.get('manufacture'), '%Y-%m').month)
            price = request.form.get('price')
            description = request.form.get('description')
            
            car.make = make
            car.model = model
            car.engine_power = engine_power
            car.engine_capacity = engine_capacity
            car.body_type = body
            car.fuel_type = fuel
            car.gearbox = gearbox
            car.number_of_doors = num_doors
            car.mileage = mileage
            car.steering_wheel_side = steering
            car.color = color
            car.pyear = year
            car.prod_month = month
            car.price = price
            car.status = "Proposition_change"
            car.description = description
            car.created_at = datetime.datetime.utcnow()
            car.modified_at = datetime.datetime.utcnow()
            db.session.add(car)
            db.session.commit()
            return redirect('/admin/confirming')

        return self.render('admin/change.html', car=car, options=options)
    
    @expose('/discard/<int:id_of_car>/', methods=['GET', 'POST'])
    def discard(current_user, id_of_car):
        car = Car.query.filter_by(id=id_of_car).first()
        car.status = "Discarded"
        db.session.commit()
        return redirect('/admin/confirming')

admin = Admin(app, name="JPManage", index_view=MyAdminIndexView(), template_mode='bootstrap3')
admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Car, db.session))
admin.add_view(MyModelView(Makes, db.session))
admin.add_view(MyModelView(Models, db.session))
admin.add_view(MyModelView(Body, db.session))
admin.add_view(MyModelView(Fuel, db.session))
admin.add_view(MyModelView(Gearbox, db.session))
admin.add_view(MyModelView(NumDoors, db.session))
admin.add_view(MyModelView(WheelSide, db.session))
admin.add_view(MyModelView(Color, db.session))
admin.add_view(MyModelView(Options, db.session))
admin.add_view(MyModelView(Question, db.session))
admin.add_view(RegressorView(name='Regressor-2', endpoint='regressor'))
admin.add_view(Regressor1View(name='Regressor-1', endpoint='regressor1'))
admin.add_view(Confirmads(name='Confirming', endpoint='confirming'))
admin.add_view(Arrived(name='Arriving', endpoint='arriving'))
admin.add_view(ConfirmRequests(name='Delete Accounts', endpoint='deleting'))

@mainweb.route('/', methods=['GET','POST'])
def index():
    return render_template('index.html')

@mainweb.route('/search', methods=['GET','POST'])
def search():
    makes = Makes.query.all()
    models = Models.query.all()
    bodys = Body.query.all()
    fuels = Fuel.query.all()
    gearboxes = Gearbox.query.all()
    doors = NumDoors.query.all()
    colors = Color.query.all()
    
    now = datetime.datetime.now()
    yearsf = list(range(1996, int(now.year)+1))
    yearst = list(range(int(now.year)+1, 1996, -1))
    prices = [150, 300, 500, 1000, 1500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000, 9000, 10000, 12500, 15000, 17500, 25000, 30000, 40000, 50000, 60000, 70000]
    pricef = list(prices)
    pricet = list(reversed(prices))
    models = list(['------'])
    form = SearchForm()
    form.make.choices = [(make.make, make.make) for make in makes]
    form.model.choices = [(model, model) for model in models]
    form.body.choices = [(body.body, body.body) for body in Body.query.all()]
    form.fuel.choices = [(fuel.fuel, fuel.fuel) for fuel in Fuel.query.all()]
    form.gearbox.choices = [(gearbox.gearbox, gearbox.gearbox) for gearbox in Gearbox.query.all()]
    form.num_doors.choices = [(num_doors.doors, num_doors.doors) for num_doors in NumDoors.query.all()]
    form.color.choices = [(color.color, color.color) for color in Color.query.all()]
    form.yearfrom.choices = [(year, year) for year in yearsf]
    form.yearto.choices = [(year, year) for year in yearst]
    form.pricefrom.choices = [(price, price) for price in pricef]
    form.priceto.choices = [(price, price) for price in pricet]
    if request.method == 'POST':
        make = request.form.get('make')
        model = request.form.get('model')
        body = request.form.get('body')
        fuel = request.form.get('fuel')
        gearbox = request.form.get('gearbox')
        num_doors = request.form.get('num_doors')
        steering = request.form.get('steering')
        color = request.form.get('color')
        pricefrom = request.form.get('pricefrom')
        priceto = request.form.get('priceto')
        yearfrom = request.form.get('yearfrom')
        yearto = request.form.get('yearto')
 
        empty = Car.query.filter_by(make="empty").all()
        cars = cars = Car.query.filter((Car.status == 'Confirmed') | (Car.status == 'Arrived'))
        if make != '------':
            cars = cars.filter(Car.make == make)
        if model != '------':
            cars = cars.filter(Car.model == model)
        if gearbox != '------':
            cars = cars.filter(Car.gearbox == gearbox)
        if fuel != '------':
            cars = cars.filter(Car.fuel_type == fuel)
        if body != '------':
            cars = cars.filter(Car.body_type == body)
        if color != '------':
            cars = cars.filter(Car.color == color)
        cars = cars.filter(Car.price >= pricefrom) 
        cars = cars.filter(Car.price <= priceto)
        cars = cars.filter(Car.pyear >= yearfrom)
        cars = cars.filter(Car.pyear <= yearto)
        cars = cars.filter((Car.status == 'Confirmed') | (Car.status == 'Arrived'))
        cars = cars.all()

        return render_template('searcheresults.html', cars=cars, empty=empty,)
    return render_template('search.html',  form=form)



@mainweb.route('/profile')
@login_required
def profile():
    img_file = url_for('static', filename='profile_pictures/' + current_user.image_file)
    return render_template('profile.html', title="Profile", current_user=current_user, img_file=img_file)

@mainweb.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        question = Question() 
        question.email = email
        question.name = name
        question.subj = subject
        question.message = message
        db.session.add(question)
        db.session.commit()
        flash('Question sent successfully')
        return render_template('contacts.html', title="Contact")
    return render_template('contacts.html', title="Contact")
@mainweb.route('/faq')
def faq():
    questions = Question.query.filter(Question.isconfirmed).all()
    return render_template('faq.html', title="faq", questions=questions)

@mainweb.route('/privacy_policy')
def policy():
    return render_template('privacy_policy.html', title="privacy policy")

@mainweb.route('/requestdelete', methods=['GET', 'POST'])
@login_required
def requestdelete():
    if request.method == 'POST':
        message = request.form.get('reason')
        
        requestdel = RequestDelete() 
        requestdel.user_id = current_user.get_id()
        requestdel.reason = message
        db.session.add(requestdel)
        db.session.commit()
        flash('Request successfully sent')
        return redirect('/')
    return render_template('requestdelete.html', title="Contact")


@mainweb.route('/mycars')
@login_required
def mycars():
    empty = Car.query.filter_by(make="empty").all()
    cars = Car.query.filter_by(owner_id=current_user.get_id()).all()
    return render_template('mycars.html', cars=cars, empty=empty)

@mainweb.route('/confirm/<int:id_of_car>/', methods=['GET', 'POST'])
def confirm(id_of_car):
    car = Car.query.filter_by(id=id_of_car).first()
    car.status = "Confirmed"
    db.session.commit()
    return redirect('/mycars')


@mainweb.route('/delete/<int:id_of_car>/', methods=['GET', 'POST'])
def delete(id_of_car):
    car = Car.query.filter_by(id=id_of_car).first()
    if car.owner_id == current_user.get_id():
        db.session.delete(car)
        db.session.commit()
        return redirect('/mycars')
    return redirect('/mycars')

@mainweb.route('/details/<int:id_of_car>/', methods=['GET', 'POST'])
def details(id_of_car):
    car = Car.query.filter_by(id=id_of_car).first()
    #if car.owner_id == current_user.get_id():
    return render_template('proposition.html', car=car)
    #else:
    #   flash('Chosen car is not your!')
    #    return redirect('/mycars')


@mainweb.route('/add_new_car', methods=['GET', 'POST'])
@login_required
def addcar():
    makes = Makes.query.all()
    models = Models.query.all()
    bodys = Body.query.all()
    fuels = Fuel.query.all()
    gearboxes = Gearbox.query.all()
    doors = NumDoors.query.all()
    wheel = WheelSide.query.all()
    colors = Color.query.all()

   
    form = UploadForm()
    form.make.choices = [(make.make, make.make) for make in Makes.query.all()]
    form.model.choices = [(model.model, model.model) for model in Models.query.filter_by(make='Toyota').all()]
    form.body.choices = [(body.body, body.body) for body in Body.query.all()]
    form.fuel.choices = [(fuel.fuel, fuel.fuel) for fuel in Fuel.query.all()]
    form.gearbox.choices = [(gearbox.gearbox, gearbox.gearbox) for gearbox in Gearbox.query.all()]
    form.num_doors.choices = [(num_doors.doors, num_doors.doors) for num_doors in NumDoors.query.all()]
    form.steering.choices = [(steering.wheel, steering.wheel) for steering in WheelSide.query.all()]
    form.color.choices = [(color.color, color.color) for color in Color.query.all()]
    
    options = Options.query.all()

    if request.method == 'POST':

        selected_options = request.form.getlist("options")

        print(selected_options)


        make = request.form.get('make')
        model = request.form.get('model')
        engine_power = request.form.get('engine_power')
        body = request.form.get('body')
        fuel = request.form.get('fuel')
        engine_capacity = request.form.get('engine_capacity')
        gearbox = request.form.get('gearbox')
        num_doors = request.form.get('num_doors')
        mileage = request.form.get('mileage')
        steering = request.form.get('steering')
        color = request.form.get('color')
        year = str(datetime.datetime.strptime(request.form.get('manufacture'), '%Y-%m').year)
        month = str(datetime.datetime.strptime(request.form.get('manufacture'), '%Y-%m').month)
        price = request.form.get('price')
        description = request.form.get('description')
        vin = request.form.get('vin')
        
        new_car = Car()
        new_car.make = make
        new_car.model = model
        new_car.engine_power = engine_power
        new_car.engine_capacity = engine_capacity
        new_car.body_type = body
        new_car.fuel_type = fuel
        new_car.gearbox = gearbox
        new_car.number_of_doors = num_doors
        new_car.mileage = mileage
        new_car.steering_wheel_side = steering
        new_car.color = color
        new_car.pyear = year
        new_car.prod_month = month
        new_car.price = price
        new_car.status = "Proposed"
        new_car.description = description
        new_car.created_at = datetime.datetime.utcnow()
        new_car.modified_at = datetime.datetime.utcnow()
        new_car.owner_id = current_user.get_id()
        new_car.VIN = vin
        db.session.add(new_car)
        
        for i in selected_options:
            option = Options.query.filter_by(id=i).first() 
            new_car.options.append(option)

        
        db.session.commit()


        for filename in request.files.getlist('photo'):
            name = "Photo" + secure_filename(filename.filename)
            file_rel = photos.save(filename, name=name + '.')
            photo_new = Photos()
            photo_new.photo_name = file_rel
            db.session.add(photo_new)
            db.session.commit()
            new_car.photos.append(photo_new)

        return render_template('proposition.html', car=new_car)
    

    iduser = current_user.get_id()

    return render_template('addcar.html', title="Add car", iduser=iduser, options=options, models=models, bodys=bodys, fuels=fuels, gearboxes=gearboxes, doors=doors, wheels=wheel, colors=colors, makes=makes, form=form, predict_func=predict)

@mainweb.route('/process/<makec>')
def process(makec):
    models = Models.query.filter_by(make=makec).all()
    modelArray = []
    for model in models:
        modelObj = {}
        modelObj['id'] = model.id
        modelObj['model'] = model.model
        modelArray.append(modelObj)

    return jsonify({'models' : modelArray})


@mainweb.route('/price1', methods=['POST'])
def price1():
    if request.method == 'POST':
        data = request.get_json()
        make = data['data']['make']
        model = data['data']['model']
        body = data['data']['body']
        fuel = data['data']['fuel']
        gearbox = data['data']['gearbox']
        color = data['data']['color']
        engine_cap = data['data']['engc']
        engine_pow = data['data']['engp']
        prod_year = datetime.datetime.strptime(data['data']['manufacture'], '%Y-%m').year
        mileage = data['data']['mileage']
        num_doors = data['data']['num_doors']
        steering = data['data']['steering']

        new_car = [{'make': make, 'model' : model, 'production_year' : prod_year, 'body_style' : body, 'num_of_doors' : num_doors, 'gearbox' : gearbox, 'fuel_type': fuel, 'engine_power' : engine_pow, 'engine_capacity' : engine_cap, 'mileage' : mileage, 'color' : color}]
        
        result1 = load_regressor('carsdataset.json', new_car)
        #result2 = load_lin_regressor('carsdataset.json', new_car)
        print(str(result1))
        return str(int(result1))



@mainweb.route('/price2', methods=['POST'])
def price2():
    if request.method == 'POST':
        data = request.get_json()
        make = data['data']['make']
        model = data['data']['model']
        body = data['data']['body']
        fuel = data['data']['fuel']
        gearbox = data['data']['gearbox']
        color = data['data']['color']
        engine_cap = data['data']['engc']
        engine_pow = data['data']['engp']
        prod_year = datetime.datetime.strptime(data['data']['manufacture'], '%Y-%m').year
        mileage = data['data']['mileage']
        num_doors = data['data']['num_doors']
        steering = data['data']['steering']

        new_car = [{'make': make, 'model' : model, 'production_year' : prod_year, 'body_style' : body, 'num_of_doors' : num_doors, 'gearbox' : gearbox, 'fuel_type': fuel, 'engine_power' : engine_pow, 'engine_capacity' : engine_cap, 'mileage' : mileage, 'color' : color}]
        
        #result1 = load_regressor('carsdataset.json', new_car)
        result2 = load_lin_regressor('carsdataset.json', new_car)
        print(str(result2))
        return  str(int(result2)) 


@mainweb.route('/price_get', methods=['GET', 'POST'])
@login_required
def price_get():
    form = UploadForm()
    if form.validate_on_submit():
        for filename in request.files.getlist('photo'):
            name = "Photo" + secure_filename(filename)
            photos.save(filename, name=name + '.')
        success = True
    else:
        success = False
    return render_template('addcar.html', title="Add car", form=form, success=success, predict_func=predict)



@mainweb.route('/manage')
def manage_file():
    files_list = os.listdir(app.config['UPLOADED_PHOTOS_DEST'])
    return render_template('manage.html', files_list=files_list)


@mainweb.route('/open/<filename>')
def open_file(filename):
    file_url = photos.url(filename)
    return render_template('browser.html', file_url=file_url)


@mainweb.route('/delete/<filename>')
def delete_file(filename):
    file_path = photos.path(filename)
    os.remove(file_path)
    return redirect(url_for('manage_file'))


authweb = Blueprint('authweb', __name__)

@authweb.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user is None or not user.check_password(request.form.get('password')):
            flash('Invalid username or password')
            return redirect(url_for('authweb.login'))
        login_user(user, remember=request.form.get('remember'))
        return redirect(url_for('mainweb.index'))
    return render_template('login.html', title='Sign In')



@authweb.route('/signup', methods=['GET', 'POST'])
def signup():
    user_check = User.query.filter_by(email=request.form.get('email')).first()
    if current_user.is_authenticated:
        return redirect(url_for('mainweb.index'))
    if request.method == 'POST':
        if user_check:
            flash('User with your email already exists')
            return redirect(url_for('authweb.signup'))
        
        user = User(email=request.form.get('email'))
        user.set_password(request.form.get('password'))
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('authweb.login'))
    return render_template('signup.html', title='Register')

@authweb.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('mainweb.index'))

@authweb.route('/forgot', methods=['GET', 'POST'])
def forgot():
    error = None
    message = None
    form = ForgotForm()
    if form.validate_on_submit():
        pass
    return render_template('forgot.html', form=form, error=error, message=message)


@authweb.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('csrf_error.html', reason=e.description), 400
@mainweb.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('csrf_error.html', reason=e.description), 400
