import tensorflow as tf
import joblib
from datetime import timedelta
import pandas as pd
import numpy as np
import sys
from keras.models import Sequential
from keras.layers import LSTM, Dense
sys.path.append('.')
from database.BuildingRepository import BuildingRepository

def create_model():
    # LSTM model
    timesteps = 1
    shape = 6
    model = Sequential()
    model.add(LSTM(units=4, input_shape=(timesteps, shape)))
    model.add(Dense(units=1))  # Use the original number of features as the output units
    model.compile(optimizer='adam', loss='mean_squared_error',metrics=['mae', 'mse'])

    return model
def prepare_data(data, time_steps):
    X, y = [], []
    for i in range(len(data) - time_steps - 2):
        X.append(data[i:i + time_steps, :-1])  # Exclude the last column (Generation)
        y.append(data[i + time_steps, -1])  # The last column (Generation) is the target
    return np.array(X), np.array(y)

def predict_saved_model(last_24_hours_data):
    model = tf.keras.models.load_model('saved_model/generation_forecast')

    # Load the scaler
    scaler = joblib.load('saved_model/scaler.pkl')
    pred_scaler = joblib.load('saved_model/pred_scaler.pkl')

    df_scaled = scaler.fit_transform(last_24_hours_data)
    
    timesteps = 1
    X_pred, y = prepare_data(df_scaled, timesteps)
    X_pred = np.reshape(X_pred, (X_pred.shape[0], timesteps, X_pred.shape[2]))
    
    y_pred = model.predict(X_pred)
    y_pred = pred_scaler.inverse_transform(y_pred)

    last = scaler.inverse_transform(df_scaled[:-3])

    df = pd.DataFrame(last, columns=['Month', 'Day', 'Hour', 'Minute', 'Generation-1', 'Generation-2', 'Generation'])
    df['Prediction'] = y_pred
    df['datetime'] = pd.to_datetime(df[['Month', 'Day', 'Hour', 'Minute']].assign(Year=2023))

    # Drop the separate columns if needed
    df.drop(['Month', 'Day', 'Hour', 'Minute'], axis=1, inplace=True)

    df.set_index("datetime", inplace=True)
    df = df.resample('1H').mean()
    df["datetime"] = df.index

    return df

def forecast_generation():
    building_repo = BuildingRepository()

    df_test = pd.DataFrame(building_repo.get_totalpower_col())
    df_test = df_test.drop("_id", axis=1)

    df_test['datetime'] = pd.to_datetime(df_test['datetime'])

    current_time = df_test['datetime'].max()
    twenty_four_hours_ago = current_time - timedelta(hours=24)

    last_24_hours_data = df_test[df_test['datetime'] >= twenty_four_hours_ago]

    last_24_hours_data['generation'] = pd.to_numeric(last_24_hours_data['totalgeneration'], errors='coerce')
    last_24_hours_data['Month'] = last_24_hours_data['datetime'].dt.month
    last_24_hours_data['Day'] = last_24_hours_data['datetime'].dt.day
    last_24_hours_data['Hour'] = last_24_hours_data['datetime'].dt.hour
    last_24_hours_data['Minute'] = last_24_hours_data['datetime'].dt.minute

    last_24_hours_data.rename(columns={'generation': 'Generation'}, inplace=True)
    last_24_hours_data.drop(['datetime', 'consumption'], axis=1, inplace=True)

    last_24_hours_data = last_24_hours_data.dropna()
    last_24_hours_data['Generation-1'] = last_24_hours_data['Generation'].shift(1)
    last_24_hours_data.loc[last_24_hours_data['Day'] != last_24_hours_data['Day'].shift(1), 'Generation-1'] = 0
    last_24_hours_data['Generation-2'] = last_24_hours_data['Generation'].shift(2)
    last_24_hours_data.loc[last_24_hours_data['Day'] != last_24_hours_data['Day'].shift(2), 'Generation-2'] = 0
    last_24_hours_data = last_24_hours_data[
        ['Month', 'Day', 'Hour', 'Minute', 'Generation-1', 'Generation-2', 'Generation']]

    return predict_saved_model(last_24_hours_data)


