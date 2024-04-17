import datetime
import time

import matplotlib as mpl
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler


def consumption_forecast(df):
    print(df)
    mpl.rcParams['figure.figsize'] = (12, 6)
    mpl.rcParams['axes.grid'] = False

    df.datetime = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S', dayfirst=True)
    df.set_index("datetime", inplace=True)
    df_init = df.resample('1H').mean()  # only works if the column "Periods" as index

    df_init["datetime"] = df_init.index
    # creating a column with week days
    df_init["day_of_week"] = df_init["datetime"].dt.day_name()
    df_init['day_of_week'] = df_init[['day_of_week']].replace(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        [0, 1, 2, 3, 4, 5, 6])
    # remove weekend
    df_init = df_init.loc[(df_init["day_of_week"] != 5) & (df_init['day_of_week'] != 6)]

    # interval of the dataset
    # df_1h = df_init["2022-03-28":].copy()
    df_1h = df_init.copy()

    df_1h = df_1h.dropna()

    a = df_1h['totalpower'][:].copy()
    a = a.to_numpy()
    new_columns = 28

    # Add "new_columns" Lagged Column
    for x in range(1, new_columns + 1):
        a = np.delete(a, len(a) - 1)  # remove the first value of the array "a" (is for the next iteration)
        a = np.append(0, a)  # add a 0 in the end of the array "a"

        if (x < 8) | (x > 24):
            nc = "t-" + str(x)  # create the name for the new column
            df_1h[nc] = a  # save values from the array "a"

    # Removing index and creating the timestamp
    df_1h["datetime"] = df_1h.index
    df_1h = df_1h.reset_index(drop=True)

    Datetime = pd.to_datetime(df_1h.pop('datetime'), format='%Y-%m-%d %H:%M:%S')
    timestamp_s = Datetime.map(datetime.datetime.timestamp)

    # Converting 1D time to 2D time
    days = 24 * 60 * 60
    year = 366 * days

    df_1h['Day sin'] = np.sin(timestamp_s * (2 * np.pi / days))
    df_1h['Day cos'] = np.cos(timestamp_s * (2 * np.pi / days))
    df_1h['Year sin'] = np.sin(timestamp_s * (2 * np.pi / year))
    df_1h['Year cos'] = np.cos(timestamp_s * (2 * np.pi / year))

    # Number of Hours and Days of the Dataset
    h = len(df_1h)
    days_Data = len(df_1h) / 24

    column_indices = {name: i for i, name in enumerate(df_1h.columns)}

    # Percentage of the Dataset that is used to Test and Train
    tst = round((0.1 * days_Data + 0.01), 0) / days_Data  # Corresponds to 21 days, which is ~10 %
    trn = round((0.7 * days_Data + 0.01), 0) / days_Data  # Corresponds to 146 days, which is ~70 %

    # Split the Dataset
    # dt = datetime.datetime.now()
    # df_train = df_1h[df_1h['day_of_week'] == dt.weekday()]
    # train_df = df_train.tail(240)
    # print(train_df)

    train_df = df_1h[0:int(h * trn)].copy()
    val_df = df_1h[int(h * trn):int(h * (1 - tst))].copy()
    # !test is train
    test_df = df_1h[int(h * (1 - trn)):].copy()
    print("h", h, "tst", tst, "int", int(h * (1 - trn)))

    num_features = df_1h.shape[1]
    # To Invert the Data Normalisation Process (END of the Code)
    X = train_df['totalpower'].copy()
    X_std = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0))

    N = df_1h['totalpower'].copy()
    N_std = (N - N.min(axis=0)) / (N.max(axis=0) - N.min(axis=0))

    # normalize data
    scaler = MinMaxScaler()
    scaler.fit(train_df)  # finds the max value of the data

    featu = df_1h.columns.to_numpy()  # ['Consumption','day_of_week',"t+1","t+2","t+3","t+4","t+5","t+6","t+7",'Day sin','Day cos','Year sin','Year cos']
    # Scale the Train, Val and Test Dataset between [0,1]
    train_df[featu] = scaler.transform(train_df)
    val_df[featu] = scaler.transform(val_df)
    test_df[featu] = scaler.transform(test_df)

    # window generator class -------------------
    class WindowGenerator:
        def __init__(self, input_width, label_width, shift,
                     train_df=train_df, val_df=val_df, test_df=test_df,
                     label_columns=None):
            # Store the raw data.
            self.train_df = train_df
            self.val_df = val_df
            self.test_df = test_df

            # Work out the label column indices.
            self.label_columns = label_columns
            if label_columns is not None:
                self.label_columns_indices = {name: i for i, name in
                                              enumerate(label_columns)}
            self.column_indices = {name: i for i, name in
                                   enumerate(train_df.columns)}

            # Work out the window parameters.
            self.input_width = input_width
            self.label_width = label_width
            self.shift = shift

            self.total_window_size = input_width + shift

            self.input_slice = slice(0, input_width)
            self.input_indices = np.arange(self.total_window_size)[self.input_slice]

            self.label_start = self.total_window_size - self.label_width
            self.labels_slice = slice(self.label_start, None)
            self.label_indices = np.arange(self.total_window_size)[self.labels_slice]

        def __repr__(self):
            return '\n'.join([
                f'Total window size: {self.total_window_size}',
                f'Input indices: {self.input_indices}',
                f'Label indices: {self.label_indices}',
                f'Label column name(s): {self.label_columns}'])

    def split_window(self, features):
        inputs = features[:, self.input_slice, :]
        labels = features[:, self.labels_slice, :]
        if self.label_columns is not None:
            labels = tf.stack(
                [labels[:, :, self.column_indices[name]] for name in self.label_columns],
                axis=-1)

        # Slicing doesn't preserve static shape information, so set the shapes
        # manually. This way the `tf.data.Datasets` are easier to inspect.
        inputs.set_shape([None, self.input_width, None])
        labels.set_shape([None, self.label_width, None])

        return inputs, labels

    WindowGenerator.split_window = split_window

    def make_dataset(self, data):
        data = np.array(data, dtype=np.float32)
        ds = tf.keras.preprocessing.timeseries_dataset_from_array(
            data=data,
            targets=None,
            sequence_length=self.total_window_size,
            sequence_stride=1,
            shuffle=True,
            batch_size=32, )

        ds = ds.map(self.split_window)

        return ds

    WindowGenerator.make_dataset = make_dataset

    @property
    def train(self):
        return self.make_dataset(self.train_df)

    @property
    def val(self):
        return self.make_dataset(self.val_df)

    @property
    def test(self):
        return self.make_dataset(self.test_df)

    @property
    def example(self):
        """Get and cache an example batch of `inputs, labels` for plotting."""
        result = getattr(self, '_example', None)
        if result is None:
            # No example batch was found, so get one from the `.train` dataset
            result = next(iter(self.train))
            # And cache it for next time
            self._example = result
        return result

    WindowGenerator.train = train
    WindowGenerator.val = val
    WindowGenerator.test = test
    WindowGenerator.example = example

    # window generator class -------------------

    # function for compile and fit the model
    MAX_EPOCHS = 30

    def compile_and_fit(model, window, patience=2):
        early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=patience, mode='min')

        model.compile(loss='mse',
                      optimizer=tf.optimizers.Adam(),
                      metrics=[tf.metrics.MeanAbsoluteError()])

        history = model.fit(window.train, epochs=MAX_EPOCHS,
                            validation_data=window.val,
                            callbacks=[early_stopping], run_eagerly= True)
        return history

    # multistepforecast
    # def forecastday():
    OUT_STEPS = 24
    multi_window = WindowGenerator(input_width=24,
                                   label_width=OUT_STEPS,
                                   shift=OUT_STEPS,
                                   label_columns=['totalpower'])

    # print(f'Inputs shape (batch, time, features): {multi_window.example[0].shape}')
    # print(f'Labels shape (batch, time, features): {multi_window.example[1].shape}\n')

    CONV_WIDTH = 6
    multi_conv_model = tf.keras.Sequential([
        # Shape [batch, time, features] => [batch, CONV_WIDTH, features]
        tf.keras.layers.Lambda(lambda x: x[:, -CONV_WIDTH:, :]),
        # Shape => [batch, 1, conv_units]
        tf.keras.layers.Conv1D(256, activation='relu', kernel_size=(CONV_WIDTH)),
        # Shape => [batch, 1,  out_steps*features]
        tf.keras.layers.Dense(OUT_STEPS * num_features,
                              kernel_initializer=tf.initializers.zeros()),
        # Shape => [batch, out_steps, features]
        tf.keras.layers.Reshape([OUT_STEPS, num_features])
    ])
    tf.config.run_functions_eagerly(True)
    # Compile and Fit the model
    history = compile_and_fit(multi_conv_model, multi_window)

    # using the cnn trained to predict
    df_1h_norm = df_1h.copy()
    scaler1 = MinMaxScaler()
    scaler1.fit(df_1h)  # finds the max value of the data
    df_1h_norm[featu] = scaler.transform(df_1h)

    # using the cnn to predict the day ahead

    beg_inp = len(df_1h_norm) - 48 - 16  # Period that represent the beginning of the Day
    end_inp = len(df_1h_norm) - 24 - 16  # Period that represent the end of the Day
    print(f'Beginning: {Datetime[beg_inp]}\nEnd: {Datetime[end_inp - 1]}')

    beg_lab = end_inp  # Period that represent the beginning of the Label
    end_lab = beg_lab + 24  # Period that represent the end of the Label

    # Selecting the data from the chosen Day
    InpData = df_1h_norm[featu][beg_inp:end_inp].copy().to_numpy().reshape((1, end_inp - beg_inp, num_features))
    # LabData = df_1h_norm['totalpower'][(beg_lab):(end_lab)].copy().to_numpy().reshape((1,24,1))
    # Predictions
    predictions = multi_conv_model(InpData)

    # #PLOTTING -----------------------------------------------------------------------
    # plt.figure(figsize=(12,4))
    # #Input
    # plt.plot(Datetime[beg_inp:end_inp], InpData[0,:,0],
    #         marker='.', label='Inputs',  zorder=-10)
    # #Label
    # plt.plot(Datetime[beg_lab:end_lab], LabData[0,:,0],
    #         marker='o', label='Labels', c='#2ca02c')
    # #Predictions
    # plt.plot(Datetime[beg_lab:end_lab], predictions[0,:,0], marker='x',
    #         ls="-.", label='Predictions', c='#ff7f0e')

    # plt.ylabel('Consumption [normed]')
    # plt.xlabel('Time [h]')
    # plt.legend()

    # Invert Normalization
    x = predictions[0, :, 0] * (N.max(axis=0) - N.min(axis=0)) + N.min(axis=0)
    Pred = pd.DataFrame(x, columns=["Predicted Consumption"])
    Pred.to_excel("Predicted_Cons.xlsx")
    print(Pred.iat[1, 0])
    print(Pred)

    return Pred


# convulutional network
def forecasthour():
    CONV_WIDTH = 3  # Chose the number of periods to use to predict "label_width" hours.
    conv_window = WindowGenerator(
        input_width=CONV_WIDTH,
        label_width=1,  # number of periods that we want to predict
        shift=2,  #
        label_columns=['totalpower'])

    # criar o modelo
    conv_model = tf.keras.Sequential([
        tf.keras.layers.Conv1D(filters=17,
                               kernel_size=(CONV_WIDTH,),
                               activation='relu'),
        tf.keras.layers.Dense(units=17, activation='relu'),
        tf.keras.layers.Dense(units=1),
    ])
    print("Conv model on `conv_window`")
    print('Input shape:', conv_window.example[0].shape)
    print('Output shape:', conv_model(conv_window.example[0]).shape)

    # Compile and Fit the model
    history = compile_and_fit(conv_model, conv_window)

    LABEL_WIDTH = 1
    INPUT_WIDTH = LABEL_WIDTH + (CONV_WIDTH - 1)

    wide_conv_window = WindowGenerator(
        input_width=INPUT_WIDTH,
        label_width=LABEL_WIDTH,
        shift=2,
        label_columns=['totalpower'])

    # using the cnn trained to predict
    df_1h_norm = df_1h.copy()
    scaler1 = MinMaxScaler()
    scaler1.fit(df_1h)  # finds the max value of the data
    df_1h_norm[featu] = scaler.transform(df_1h)

    print(df_1h_norm)
    print(f'Beginning: {Datetime[len(df_1h_norm) - 4]}\nEnd: {Datetime[len(df_1h_norm) - 1]}')
    # Input and Label Indices
    # beg_inp = 10 #Period that represent the beginning of the Day
    # end_inp = 16 #Period that represent the end of the Day
    beg_inp = len(df_1h_norm) - 4
    end_inp = len(df_1h_norm) - 1
    print(df_1h_norm[beg_inp:end_inp])
    # index_lab=end_inp+1
    # print(index_lab)
    # Selecting the data from the chosen Day
    inp_data = df_1h_norm[featu][beg_inp:end_inp].copy().to_numpy().reshape((1, end_inp - beg_inp, num_features))
    # LabData = df_1h_norm['totalpower'][(index_lab)].copy().reshape((1,1,1))
    denorm = inp_data[0, :, 0] * (N.max(axis=0) - N.min(axis=0)) + N.min(axis=0)
    denorm.tofile("C:/Users/nteixeira/Downloads/Logs_forecast" + "/" + time.strftime("%Y%m%d-%H%M%S") + ".csv", sep=";")
    print(inp_data)
    # Predictions
    predictions = conv_model(inp_data)

    # # #PLOTTING -----------------------------------------------------------------------
    # plt.figure(figsize=(12,4))
    # #Input
    # plt.plot(Datetime[beg_inp:end_inp], inp_data[0,:,0],
    #         marker='.', label='Inputs',  zorder=-10)
    # #Label
    # plt.scatter(Datetime[index_lab], LabData[0,0,0],
    #         marker='o', label='Labels', c='#2ca02c')
    # #Predictions
    # plt.plot(Datetime[index_lab], predictions[0,0,0], marker='x',
    #         ls="-.", label='Predictions', c='#ff7f0e')

    # plt.ylabel('Consumption [normed]')
    # plt.xlabel('Time [h]')
    # plt.legend()

    # Invert Normalization
    x = predictions[0, :, 0] * (N.max(axis=0) - N.min(axis=0)) + N.min(axis=0)
    Pred = pd.DataFrame(x, columns=["Predicted Consumption"])
    # print(Pred.iat[0, 0])
    # print(Pred)

    building_repo.insert_forecast(str(Pred.iat[0, 0]), datetime.datetime.now() + datetime.timedelta(minutes=45))
    return Pred
