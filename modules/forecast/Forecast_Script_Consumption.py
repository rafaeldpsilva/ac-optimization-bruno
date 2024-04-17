import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler

def ForecastDay_Cons(consumption):
    # -------------------------------------------------------INITIAL DATA TREATMENT-------------------------------------------------------
    ###Data Cleaning-----------------------------------------------------------------------
    # Convert column 'Periods' type to datetime64
    consumption['Periods'] = pd.to_datetime(consumption['Periods'], format='%Y-%m-%d %H:%M:%S', dayfirst=True)
    consumption.set_index("Periods", inplace=True)
    df_init = consumption.resample('1H').mean()
    df_init = df_init.dropna()
    # Creating a column with weekdays
    df_init["Datetime"] = (df_init.index)
    df_init['day_of_week'] = df_init['Datetime'].dt.day_name()
    # Replace the name of the Weekdays to numbers
    df_init['day_of_week'] = df_init[['day_of_week']].replace(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], [0, 1, 2, 3, 4, 5, 6])
    # Removing the Weekend days
    df_init = df_init.loc[(df_init['day_of_week'] != 5) & (df_init['day_of_week'] != 6)]
    # Defining the interval of the Dataset
    #df_1h = df_init[:"2020-12-31"].copy()
    df_1h = df_init.copy()
    ###Creating Lagged columns from Consumption--------------------------------------------
    a = df_1h['Consumption'][:].copy()
    a = a.to_numpy()
    new_columns = 28
    # Add "new_columns" Lagged Column
    for x in range(1, new_columns + 1):
        a = np.delete(a, len(a) - 1)  # remove the first value of the array "a" (is for the next iteration)
        a = np.append(0, a)  # add a 0 in the end of the array "a"
        if ((x < 8) | (x > 24)):
            nc = "t-" + str(x)  # create the name for the new column
            df_1h[nc] = a  # save values from the array "a"

    ###Converting 1D time to 2D time------------------------------------------------------
    # Removing index and creating the timestamp
    df_1h["Datetime"] = (df_1h.index)
    df_1h = df_1h.reset_index(drop=True)
    Datetime = pd.to_datetime(df_1h.pop('Datetime'), format='%Y-%m-%d %H:%M:%S')
    timestamp_s = Datetime.map(datetime.datetime.timestamp)
    # Conversion
    days = 24 * 60 * 60  # seconds per day
    year = 365 * days  # seconds per year
    df_1h['Day sin'] = np.sin(timestamp_s * (2 * np.pi / days))
    df_1h['Day cos'] = np.cos(timestamp_s * (2 * np.pi / days))
    df_1h['Year sin'] = np.sin(timestamp_s * (2 * np.pi / year))
    df_1h['Year cos'] = np.cos(timestamp_s * (2 * np.pi / year))
    num_features = df_1h.shape[1]  # Number of columns

    ###Data Spliting------------------------------------------------------------------------
    # Total number of Hours and Days of the Dataset
    h = len(df_1h)
    days_Data = h / 24
    column_indices = {name: i for i, name in enumerate(df_1h.columns)}
    # Percentage of the Dataset that is used to Test and Train
    tst = round((0.1 * days_Data + 0.01), 0) / days_Data  # Corresponds to 21 days, which is ~10 %
    trn = round((0.7 * days_Data + 0.01), 0) / days_Data  # Corresponds to 146 days, which is ~70 %
    # Split the Dataset
    train_df = df_1h[0:int(h * trn)].copy()
    val_df = df_1h[int(h * trn):int(h * (1 - tst))].copy()

    #! CHANGED TST TO TRN
    test_df = df_1h[int(h * (1 - trn)):].copy()

    ###Data Normalization------------------------------------------------------------------------
    # Data invert the Data Normalization (To obtain the real values resulted from the Forecasting)
    N = df_1h['Consumption'].copy()
    N_std = (N - N.min(axis=0)) / (N.max(axis=0) - N.min(axis=0))
    X = train_df['Consumption'].copy()
    X_std = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0))
    # Normalization Process
    scaler = MinMaxScaler()
    scaler.fit(train_df)  # finds the max value of the data
    featu = df_1h.columns.to_numpy()
    # Scale the Train, Val and Test Dataset between [0,1]
    train_df[featu] = scaler.transform(train_df)
    val_df[featu] = scaler.transform(val_df)
    test_df[featu] = scaler.transform(test_df)

    # -------------------------------------------------------DATA WINDOWING-------------------------------------------------------
    ###Indexes and offsets-------------------------------------------------------
    class WindowGenerator():
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

    ###Split Window-------------------------------------------------------
    def split_window(self, features):
        """ split the data in windows.
                  Args:
                      features: array to split.
                  Return:
                      (tuple) with inputs and labels.
        """
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

    ###Plot-------------------------------------------------------
    def plot(self, model=None, plot_col='Consumption', max_subplots=3):
        inputs, labels = self.example
        plt.figure(figsize=(12, 8))
        plot_col_index = self.column_indices[plot_col]
        max_n = min(max_subplots, len(inputs))

        for n in range(max_n):
            plt.subplot(max_n, 1, n + 1)
            plt.ylabel(f'{plot_col} [normed]')
            plt.plot(Datetime[self.input_indices], inputs[n, :, plot_col_index],
                     label='Inputs', marker='.', zorder=-10)

            if self.label_columns:
                label_col_index = self.label_columns_indices.get(plot_col, None)
            else:
                label_col_index = plot_col_index

            if label_col_index is None:
                continue

            plt.scatter(Datetime[self.label_indices], labels[n, :, label_col_index]
                        , marker='o', label='Labels', c='#2ca02c')
            if model is not None:
                predictions = model(inputs)
                plt.plot(Datetime[self.label_indices], predictions[n, :, label_col_index],
                         marker='x', ls="-.", label='Predictions',
                         c='#ff7f0e')

            if n == 0:
                plt.legend()

        plt.xlabel('Time [h]')

    ###Create tf.data.Datasets-------------------------------------------------------
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

    WindowGenerator.split_window = split_window
    WindowGenerator.plot = plot
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
    # -------------------------------------------------------------PREPARE THE CONVOLUTION NEUARAL NETWORK - DAY-AHEAD-------------------------------------------------------------
    # function that allows you to compile and fit a given model
    MAX_EPOCHS = 30

    def compile_and_fit(model, window, patience=3):
        early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=patience, mode='min')
        model.compile(loss='mse',
                      optimizer=tf.optimizers.Adam(),
                      metrics=[tf.metrics.MeanAbsoluteError()])
        history = model.fit(window.train, epochs=MAX_EPOCHS,
                            validation_data=window.val,
                            callbacks=[early_stopping],
                            verbose=0)
        return history

    ###Creating CNN modelday-ahead)------------------------------------------------------------------------
    # Creating Window
    OUT_STEPS = 24  # Number of periods that we want to predict
    SHIFT = 24  # Number periods ahead of the last period considered in the input
    InputDays = 1
    multi_window = WindowGenerator(input_width=24,
                                   label_width=OUT_STEPS,
                                   shift=OUT_STEPS,
                                   label_columns=['Consumption'])
    # Day-ahead CNN Model
    CONV_WIDTH = 24
    multi_conv_model = tf.keras.Sequential([
        # Shape [batch, time, features] => [batch, CONV_WIDTH, features]
        tf.keras.layers.Lambda(lambda x: x[:, -CONV_WIDTH:, :]),
        # Shape => [batch, 1, conv_units]
        tf.keras.layers.Conv1D(256, activation='relu', kernel_size=(CONV_WIDTH)),
        # Shape => [batch, 1,  out_steps*features]
        tf.keras.layers.Dense(OUT_STEPS * num_features,
                              kernel_initializer=tf.initializers.zeros()),
        # Shape => [batch, out_steps, features]
        tf.keras.layers.Reshape([OUT_STEPS, num_features])])

    # Compile and Fit the model
    history = compile_and_fit(multi_conv_model, multi_window)

    # PLOTTING DAY-AHEAD-----------------------------------------------------------------------
    # Forecasting Data
    df_1h_norm = df_1h.copy()
    scaler1 = MinMaxScaler()
    scaler1.fit(df_1h)  # finds the max value of the data
    df_1h_norm[featu] = scaler.transform(df_1h)

    # Input and Label Indices
    #! CHANGE 1824 to 0
    beg_inp = 0  # Period that represent the beginning of the Day
    end_inp = beg_inp + 24  # Period that represent the end of the Day
    beg_lab = end_inp  # Period that represent the beginning of the Label
    end_lab = beg_lab + 24  # Period that represent the end of the Label
    # Selecting the data from the chosen Day
    InpData = df_1h_norm[featu][beg_inp:end_inp].copy().to_numpy().reshape((1, end_inp - beg_inp, num_features))
    LabData = df_1h_norm['Consumption'][(beg_lab):(end_lab)].copy().to_numpy().reshape((1, 24, 1))
    # Predictions
    predictions = multi_conv_model(InpData)

    # Invert Normalization
    x = predictions[0, :, 0] * (N.max(axis=0) - N.min(axis=0)) + N.min(axis=0)

    return x


"""#Hour-ahead Forecast"""


def ForecastHour_Cons(Consumption):
    # -------------------------------------------------------INITIAL DATA TREATMENT-------------------------------------------------------
    ###Data Cleaning-----------------------------------------------------------------------
    # Convert column 'Periods' type to datetime64
    Consumption.Periods = pd.to_datetime(Consumption['Periods'], format='%Y-%m-%d %H:%M:%S', dayfirst=True)
    Consumption.set_index("Periods", inplace=True)
    df_init = Consumption.resample('1H').mean()
    # Creating a column with weekdays
    df_init["Datetime"] = (df_init.index)
    df_init['day_of_week'] = df_init['Datetime'].dt.day_name()
    # Replace the name of the Weekdays to numbers
    df_init['day_of_week'] = df_init[['day_of_week']].replace(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], [0, 1, 2, 3, 4, 5, 6])
    # Removing the Weekend days
    df_init = df_init.loc[(df_init['day_of_week'] != 5) & (df_init['day_of_week'] != 6)]
    # Defining the interval of the Dataset
    df_1h = df_init[:"2020-12-31"].copy()

    ###Creating Lagged columns from Consumption--------------------------------------------
    a = df_1h['Consumption'][:].copy()
    a = a.to_numpy()
    new_columns = 28
    # Add "new_columns" Lagged Column
    for x in range(1, new_columns + 1):
        a = np.delete(a, len(a) - 1)  # remove the first value of the array "a" (is for the next iteration)
        a = np.append(0, a)  # add a 0 in the end of the array "a"
        if ((x < 8) | (x > 24)):
            nc = "t-" + str(x)  # create the name for the new column
            df_1h[nc] = a  # save values from the array "a"

    ###Converting 1D time to 2D time------------------------------------------------------
    # Removing index and creating the timestamp
    df_1h["Datetime"] = (df_1h.index)
    df_1h = df_1h.reset_index(drop=True)
    Datetime = pd.to_datetime(df_1h.pop('Datetime'), format='%Y-%m-%d %H:%M:%S')
    timestamp_s = Datetime.map(datetime.datetime.timestamp)
    # Conversion
    days = 24 * 60 * 60  # seconds per day
    year = 365 * days  # seconds per year
    df_1h['Day sin'] = np.sin(timestamp_s * (2 * np.pi / days))
    df_1h['Day cos'] = np.cos(timestamp_s * (2 * np.pi / days))
    df_1h['Year sin'] = np.sin(timestamp_s * (2 * np.pi / year))
    df_1h['Year cos'] = np.cos(timestamp_s * (2 * np.pi / year))
    num_features = df_1h.shape[1]  # Number of columns

    ###Data Spliting------------------------------------------------------------------------
    # Total number of Hours and Days of the Dataset
    h = len(df_1h)
    days_Data = h / 24
    column_indices = {name: i for i, name in enumerate(df_1h.columns)}
    # Percentage of the Dataset that is used to Test and Train
    tst = round((0.1 * days_Data + 0.01), 0) / days_Data  # Corresponds to 21 days, which is ~10 %
    trn = round((0.7 * days_Data + 0.01), 0) / days_Data  # Corresponds to 146 days, which is ~70 %
    # Split the Dataset
    train_df = df_1h[0:int(h * trn)].copy()
    val_df = df_1h[int(h * trn):int(h * (1 - tst))].copy()
    test_df = df_1h[int(h * (1 - tst)):].copy()

    ###Data Normalization------------------------------------------------------------------------
    # Data invert the Data Normalization (To obtain the real values resulted from the Forecasting)
    N = df_1h['Consumption'].copy()
    N_std = (N - N.min(axis=0)) / (N.max(axis=0) - N.min(axis=0))
    X = train_df['Consumption'].copy()
    X_std = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0))
    # Normalization Process
    scaler = MinMaxScaler()
    scaler.fit(train_df)  # finds the max value of the data
    featu = df_1h.columns.to_numpy()
    # Scale the Train, Val and Test Dataset between [0,1]
    train_df[featu] = scaler.transform(train_df)
    val_df[featu] = scaler.transform(val_df)
    test_df[featu] = scaler.transform(test_df)

    # -------------------------------------------------------DATA WINDOWING-------------------------------------------------------
    ###Indexes and offsets-------------------------------------------------------
    class WindowGenerator():
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

    ###Split Window-------------------------------------------------------
    def split_window(self, features):
        """ split the data in windows.
                  Args:
                      features: array to split.
                  Return:
                      (tuple) with inputs and labels.
        """
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

    ###Plot-------------------------------------------------------
    def plot(self, model=None, plot_col='Consumption', max_subplots=3):
        inputs, labels = self.example
        plt.figure(figsize=(12, 8))
        plot_col_index = self.column_indices[plot_col]
        max_n = min(max_subplots, len(inputs))

        for n in range(max_n):
            plt.subplot(max_n, 1, n + 1)
            plt.ylabel(f'{plot_col} [normed]')
            plt.plot(Datetime[self.input_indices], inputs[n, :, plot_col_index],
                     label='Inputs', marker='.', zorder=-10)

            if self.label_columns:
                label_col_index = self.label_columns_indices.get(plot_col, None)
            else:
                label_col_index = plot_col_index

            if label_col_index is None:
                continue

            plt.scatter(Datetime[self.label_indices], labels[n, :, label_col_index]
                        , marker='o', label='Labels', c='#2ca02c')
            if model is not None:
                predictions = model(inputs)
                plt.plot(Datetime[self.label_indices], predictions[n, :, label_col_index],
                         marker='x', ls="-.", label='Predictions',
                         c='#ff7f0e')

            if n == 0:
                plt.legend()

        plt.xlabel('Time [h]')

    ###Create tf.data.Datasets-------------------------------------------------------
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

    WindowGenerator.split_window = split_window
    WindowGenerator.plot = plot
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
    # -------------------------------------------------------------PREPARE THE CONVOLUTION NEUARAL NETWORK - HOUR-AHEAD-------------------------------------------------------------
    # function that allows you to compile and fit a given model
    MAX_EPOCHS = 30

    def compile_and_fit(model, window, patience=3):
        early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=patience, mode='min')
        model.compile(loss='mse',
                      optimizer=tf.optimizers.Adam(),
                      metrics=[tf.metrics.MeanAbsoluteError()])
        history = model.fit(window.train, epochs=MAX_EPOCHS,
                            validation_data=window.val,
                            callbacks=[early_stopping],
                            verbose=0)
        return history

    ###Creating CNN model (1 hour-ahead)------------------------------------------------------------------------
    # Creating Window
    CONV_WIDTH = 6  # Chose the number of periods to use to predict "label_width" periods.
    x = 1  # Number of periods that we want to predict
    y = 1  # Number periods ahead of the last period considered in the input
    # (e.g. if last period is 5,x=3,y=2;Then he forecasted values will belong to period 8,9,10, ignoring the period 6 and 7)
    conv_window = WindowGenerator(
        input_width=x + (CONV_WIDTH - 1),
        label_width=x,  # Number of periods that we want to predict
        shift=x + y,  # Number periods ahead of the last period considered in the input
        label_columns=['Consumption'])
    # Hour-ahead CNN Model
    conv_model = tf.keras.Sequential([
        tf.keras.layers.Conv1D(filters=17,
                               kernel_size=(CONV_WIDTH,), activation='relu'),
        tf.keras.layers.Dense(units=17, activation='relu'),
        tf.keras.layers.Dense(units=1), ])

    # Compile and Fit the model
    history = compile_and_fit(conv_model, conv_window);

    # PLOTTING HOUR-AHEAD-----------------------------------------------------------------------
    df_1h_norm = df_1h.copy()
    scaler1 = MinMaxScaler()
    scaler1.fit(df_1h)  # finds the max value of the data
    df_1h_norm[featu] = scaler.transform(df_1h)
    # Input and Label Indices
    beg_inp = 3000  # Period that represent the beginning of the Day
    end_inp = 1 + 3006  # Period that represent the end of the Day
    index_lab = end_inp + 1

    # Selecting the data from the chosen Day
    InpData = df_1h_norm[featu][beg_inp:end_inp].copy().to_numpy().reshape((1, end_inp - beg_inp, num_features))
    LabData = df_1h_norm['Consumption'][(index_lab)].copy().reshape((1, 1, 1))
    # Predictions
    predictions = conv_model(InpData)

    # Invert Normalization
    x = predictions[0, 0, 0] * (N.max(axis=0) - N.min(axis=0)) + N.min(axis=0)

    return x
