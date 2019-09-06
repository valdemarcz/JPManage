import json, csv, pickle
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.preprocessing import LabelBinarizer
from keras.wrappers.scikit_learn import KerasClassifier
from sklearn.preprocessing import MinMaxScaler, Imputer, OneHotEncoder
from sklearn.preprocessing import StandardScaler
from tensorflow.python.keras.models import Sequential, model_from_json
from tensorflow.python.keras.layers import Dense
from tensorflow.python.keras.wrappers.scikit_learn import KerasRegressor
from keras.models import load_model
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt


class DataFrameSelector(BaseEstimator, TransformerMixin):
  def __init__(self, attribute_names):
    self.attribute_names = attribute_names
  def fit(self, X, y=None):
    return self
  def transform(self, X):
    return X[self.attribute_names].values


num_attribs = ['production_year', 'num_of_doors', 'engine_power', 'mileage']
cat_attribs = ['make', 'model', 'body_style', 'gearbox', 'fuel_type', 'color']


num_pipeline = Pipeline([
    ('selector', DataFrameSelector(num_attribs)),
    ('attribs_adder', StandardScaler()),
])

cat_pipeline = Pipeline([
    ('selector', DataFrameSelector(cat_attribs)),
    ('cat_encoder', OrdinalEncoder()),
])

full_pipeline = FeatureUnion(transformer_list=[
    ("num_pipeline", num_pipeline),
    ("cat_pipeline", cat_pipeline),
])


def get_plain_data_from_json(filename):
    dataset = []
    with open('data/' + filename, 'r') as f:
        for line in f:
            jsonfile = json.loads(line[:-2])
            dataset.append(jsonfile)
    f.close()
    return dataset

def write(filename):
    with open(filename, 'w') as outfile:
	    json.dump("asssas", outfile)

def clear_and_load_data(filename):
    dataset = get_plain_data_from_json(filename)
    cars = pd.DataFrame(dataset)
    cars = cars.drop(cars[(cars['price']>30000) & (cars['price']<300000)].index)
    cars.drop(['engine_capacity'], axis=1)
    return cars

def data_for_prediction_object_preproessing(cars):
    unique_makes = cars.make.unique()
    unique_models = cars.model.unique()
    unique_colors = cars.color.unique()
    unique_body_style = cars.body_style.unique()
    unique_fueltype = cars.fuel_type.unique()
    unique_gearboxes = cars.gearbox.unique()

    data = {'make' : list(unique_makes), 'model' : list(unique_models), 'color' : list(unique_colors), 'body_style' : list(unique_body_style), 'fuel_type' : list(unique_fueltype), 'gearbox' : list(unique_gearboxes)}
    with open('conversion2.json', 'w') as outfile:
	    json.dump(data, outfile)



def train_regressor(filename, epochs, neuron_num):
    dataset = []
    with open(filename, 'r') as f:
        for line in f:
            jsonfile = json.loads(line[:-2])
            dataset.append(jsonfile)
    f.close()
  
    cars = pd.DataFrame(dataset)
    cars = cars.drop(cars[(cars['price']>30000) & (cars['price']<300000)].index)
    cars_prices = cars["price"].copy()
    cars = cars.drop("price", axis=1)
    cars_prepared = full_pipeline.fit_transform(cars)




    model = Sequential()
    model.add(Dense(8, input_dim=10, kernel_initializer = 'normal', activation='relu'))
    model.add(Dense(neuron_num, activation='relu'))
    model.add(Dense(1, activation='linear'))
    model.compile(loss='mse', optimizer='adam', metrics=['mae'])
    history = model.fit(cars_prepared, cars_prices, epochs=epochs, batch_size=50, verbose=1, validation_split=0.2)
    model_json = model.to_json()
    
    plt.plot(history.history['mean_absolute_error'])
    plt.plot(history.history['val_mean_absolute_error'])
    plt.title('model mean_absolute_error')
    plt.ylabel('mean_absolute_error')
    plt.xlabel('epok')
    plt.legend(['train', 'validation'], loc='upper left')
    plt.savefig('app/web/static/history.png')

    with open('neuralnetregressor.json', 'w') as json_file:
        json_file.write(model_json)
        model.save_weights('neuralnetregressor.h5')


def load_lin_regressor(filename, newobj):
    loaded_model = pickle.load(open('lin_reg.sav', 'rb'))
    dataset = []
    with open(filename, 'r') as f:
        for line in f:
            jsonfile = json.loads(line[:-2])
            dataset.append(jsonfile)
    f.close()
  
    cars = pd.DataFrame(dataset)
    cars = cars.drop(cars[(cars['price']>30000) & (cars['price']<300000)].index)
    cars_prices = cars["price"].copy()
    cars = cars.drop("price", axis=1)
    
    new_car = pd.DataFrame(newobj)

    cars = cars.append(new_car)

    cars_prepared = full_pipeline.fit_transform(cars)
    result = loaded_model.predict(cars_prepared[-1].reshape((1,-1)))
    return result

def load_regressor(filename, newobj):
    dataset = []
    with open(filename, 'r') as f:
        for line in f:
            jsonfile = json.loads(line[:-2])
            dataset.append(jsonfile)
    f.close()
  
    cars = pd.DataFrame(dataset)
    cars = cars.drop(cars[(cars['price']>30000) & (cars['price']<300000)].index)
    cars_prices = cars["price"].copy()
    cars = cars.drop("price", axis=1)
    
    new_car = pd.DataFrame(newobj)

    cars = cars.append(new_car)

    cars_prepared = full_pipeline.fit_transform(cars)


    json_file = open('neuralnetregressor.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    loaded_model.load_weights("neuralnetregressor.h5")
    loaded_model.compile(loss='mean_absolute_error', optimizer='adam', metrics=['mae'])

    daaa = np.array(cars_prepared[-1, :11])
    #loaded_model.predict(cars_prepared)
    return loaded_model.predict(cars_prepared[-1].reshape((1,-1)))


def train_lin_reg(filename):
    dataset = []
    with open(filename, 'r') as f:
        for line in f:
            jsonfile = json.loads(line[:-2])
            dataset.append(jsonfile)
    f.close()
  
    cars = pd.DataFrame(dataset)
    cars = cars.drop(cars[(cars['price']>30000) & (cars['price']<300000)].index)
    cars_prices = cars["price"].copy()
    cars = cars.drop("price", axis=1)
    cars_prepared = full_pipeline.fit_transform(cars)
    from sklearn.linear_model import LinearRegression

    lin_reg = LinearRegression()
    lin_reg.fit(cars_prepared, cars_prices)

    from sklearn.metrics import mean_absolute_error

    import numpy as np

    cars_predictions = lin_reg.predict(cars_prepared)

    lin_mae = mean_absolute_error(cars_prices, cars_predictions)

    save_filename = 'lin_reg.sav'
    pickle.dump(lin_reg, open(save_filename, 'wb'))

    return lin_mae
    
    
    '''dataset = []
    with open('data/' + filename, 'r') as f:
        for line in f:
            jsonfile = json.loads(line[:-2])
            dataset.append(jsonfile)
    f.close()
  
    cars = pd.DataFrame(dataset)
    cars = cars.drop(cars[(cars['price']>30000) & (cars['price']<300000)].index)
    cars_prices = cars["price"].copy()
    cars = cars.drop("price", axis=1)
    cars_prepared = full_pipeline.fit_transform(cars)
    '''
    #X_train, X_test, Y_train, Y_test = train_test_split(cars_prepared, cars_prices, test_size=0.2, random_state=42)
    
    
def predict(loaded_model, object_for_predict):
  
    predicted_value = loaded_model.predict(object_for_predict)
    return predicted_value

def data_transform(data):
    transformed_data = full_pipeline.fit_transform(data)
    return transformed_data