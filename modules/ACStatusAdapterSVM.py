import pickle


def calculate_heat_index_custom_celsius(temperature, relative_humidity):
    
    temperature = temperature / 10 
    relative_humidity = relative_humidity / 1000
    
    c1 = -8.785
    c2 = 1.611
    c3 = 2.339
    c4 = -0.146
    c5 = -0.01231
    c6 = -0.01642
    c7 = .002212
    c8 = .0007255
    c9 = 0.000003582

    HI = (
            c1
            + c2 * temperature
            + c3 * relative_humidity
            + c4 * temperature * relative_humidity
            + c5 * temperature * temperature
            + c6 * relative_humidity * relative_humidity
            + c7 * temperature * temperature * relative_humidity
            + c8 * temperature * relative_humidity * relative_humidity
            + c9 * temperature * temperature * relative_humidity * relative_humidity
    )
    return round(HI* 10, 2)


def predict_ac_status(outside_temp, temperature, humidity, heat_index, occupation):
    # Previsão com base nos valores inseridos
    outside_temp = float(outside_temp)
    temperature = float(temperature)
    heat_index = float(heat_index)
    humidity = float(humidity)
    occupation = int(occupation)

    # Load the model from the file
    model_filename = './modules/ACStatus/svm_model2.pkl'
    with open(model_filename, 'rb') as model_file:
        svm_model = pickle.load(model_file)
        
    # Load the model from the file
    model_filename = './modules/ACStatus/scaler2.pkl'
    with open(model_filename, 'rb') as model_file:
        scaler = pickle.load(model_file)

    prediction = svm_model.predict(scaler.transform([[outside_temp, temperature, humidity, heat_index, occupation]]))

    return prediction[0]
